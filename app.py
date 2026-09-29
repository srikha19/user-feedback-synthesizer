import asyncio
import json
import os
import re
import threading
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request
from groq import Groq
from hindsight_client import Hindsight

load_dotenv()

app = Flask(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HINDSIGHT_API_KEY = os.getenv("HINDSIGHT_API_KEY")
HINDSIGHT_API_URL = os.getenv(
    "HINDSIGHT_API_URL",
    "https://api.hindsight.vectorize.io",
)

BANK_ID = "feedback-demo-v2"
MODEL = "openai/gpt-oss-120b"
NO_INFO = "Not enough customer feedback is available."

CATEGORIES = (
    "Search Performance, Checkout & Payments, App Stability, "
    "Onboarding & Support, UI/UX, Pricing & Billing, Other"
)

LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "feedback_log.json")
log_lock = threading.Lock()

groq_client = Groq(api_key=GROQ_API_KEY)


# -----------------------------
# Helpers
# -----------------------------

def new_hindsight_client():
    return Hindsight(
        api_key=HINDSIGHT_API_KEY,
        base_url=HINDSIGHT_API_URL,
    )


def ask_llm(prompt: str) -> str:
    response = groq_client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
    )
    return (response.choices[0].message.content or "").strip()


def retain_memory(content: str):
    client = new_hindsight_client()

    if hasattr(client, "aretain"):
        async def _retain():
            return await client.aretain(bank_id=BANK_ID, content=content)

        return asyncio.run(_retain())

    return client.retain(bank_id=BANK_ID, content=content)


def recall_memories(question: str):
    async def _recall():
        client = new_hindsight_client()
        return await client.arecall(bank_id=BANK_ID, query=question)

    return asyncio.run(_recall())


def load_log():
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_log(entries):
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)


def extract_field(text: str, field: str) -> str:
    pattern = rf"\*{{0,2}}{field}\s*\*{{0,2}}\s*:\s*\*{{0,2}}\s*(.+)"
    match = re.search(pattern, text, re.IGNORECASE)
    if not match:
        return ""
    return match.group(1).strip().strip("*").strip()


def normalize_sentiment(value: str) -> str:
    v = value.lower()
    if "negative" in v:
        return "negative"
    if "positive" in v:
        return "positive"
    return "neutral"


def normalize_category(category: str, issue: str) -> str:
    text = f"{category} {issue}".lower()
    if any(k in text for k in ["payment", "checkout", "upi", "billing"]):
        return "Checkout & Payments"
    if "search" in text:
        return "Search Performance"
    if any(k in text for k in ["crash", "stability"]):
        return "App Stability"
    cleaned = (category or "").strip().strip(".").title()
    return cleaned or "Other"


def parse_analysis(text: str) -> dict:
    return {
        "issue": extract_field(text, "Main issue"),
        "category": extract_field(text, "Category") or "Other",
        "sentiment": normalize_sentiment(extract_field(text, "Sentiment")),
        "summary": extract_field(text, "Short summary"),
    }


# -----------------------------
# Routes
# -----------------------------

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze_feedback():
    try:
        data = request.get_json(silent=True) or {}
        customer = (data.get("customer") or "").strip()
        feedback = (data.get("feedback") or "").strip()
        channel = (data.get("channel") or "Unknown").strip()
        date = (data.get("date") or datetime.now().strftime("%Y-%m-%d")).strip()

        if not feedback:
            return jsonify({"success": False, "error": "Please enter customer feedback."}), 400

        # Product changes are stored as memory events, not analyzed as feedback
        if channel == "Product Update":
            memory = f"""PRODUCT CHANGE
Date: {date}
Channel: Internal product update
What changed: {feedback}
"""
            retain_memory(memory)
            print("PRODUCT UPDATE STORED SUCCESSFULLY")
            return jsonify({
                "success": True,
                "customer": customer,
                "feedback": feedback,
                "analysis": "Product change recorded in memory:\n" + feedback,
            })

        prompt = f"""You are a customer feedback analysis AI.
Analyze the following customer feedback.

Customer:
{customer}

Channel:
{channel}

Feedback:
{feedback}

Return exactly these fields:
Main issue:
Category: (choose exactly one of: {CATEGORIES})
Sentiment: (Positive, Negative, or Neutral)
Short summary:

Keep the answer concise and easy to understand.
"""
        analysis = ask_llm(prompt)

        memory = f"""Customer: {customer}
Channel: {channel}
Date: {date}
Original feedback:
{feedback}

AI Analysis:
{analysis}
"""
        retain_memory(memory)
        print("FEEDBACK STORED SUCCESSFULLY")

        parsed = parse_analysis(analysis)
        entry = {
            "customer": customer,
            "feedback": feedback,
            "channel": channel,
            "date": date,
            "time": datetime.now().isoformat(timespec="seconds"),
            **parsed,
        }
        with log_lock:
            entries = load_log()
            entries.append(entry)
            save_log(entries)

        return jsonify({
            "success": True,
            "customer": customer,
            "feedback": feedback,
            "analysis": analysis,
        })

    except Exception as e:
        print("ANALYZE ERROR:", repr(e))
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/ask", methods=["POST"])
def ask_agent():
    try:
        data = request.get_json(silent=True) or {}
        question = (data.get("question") or "").strip()

        if not question:
            return jsonify({"success": False, "error": "Please enter a question."}), 400

        # 1) Answer WITHOUT memory (generic)
        generic_prompt = f"""You are a general AI assistant. You have NO access to any
company's real customer feedback data.
Answer the question below in at most 4 sentences, in a generic way.

Question: {question}
"""
        answer_without_memory = ask_llm(generic_prompt)

        # 2) Recall from Hindsight
        try:
            memories = recall_memories(question)
            memory_items = [item.text for item in memories.results]
        except Exception as e:
            if "NotFound" in type(e).__name__:
                memory_items = []
            else:
                raise

        print("HINDSIGHT MEMORIES:", len(memory_items))

        if not memory_items:
            return jsonify({
                "success": True,
                "answer": NO_INFO,
                "answer_without_memory": answer_without_memory,
                "memories": [],
            })

        memory_text = "\n\n".join(memory_items[:10])

        # 3) Answer WITH memory
        prompt = f"""You are a customer feedback intelligence agent.
Use the customer feedback memories below to answer the user's question.

CUSTOMER FEEDBACK MEMORIES:
{memory_text}

USER QUESTION:
{question}

Rules:
- Use only the available customer feedback.
- Mention specific customer names, channels, and dates when available.
- If a PRODUCT CHANGE memory exists, compare feedback before and after it.
- Keep the answer clear and brief.
- If there is not enough information, say:
{NO_INFO}
"""
        answer = ask_llm(prompt)

        return jsonify({
            "success": True,
            "answer": answer,
            "answer_without_memory": answer_without_memory,
            "memories": [m[:300] for m in memory_items[:5]],
        })

    except Exception as e:
        print("ASK ERROR:", repr(e))
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/insights")
def insights():
    try:
        with log_lock:
            # Only count entries created by the current version (they have a channel)
            entries = [e for e in load_log() if e.get("channel")]

        total = len(entries)
        negative = sum(1 for e in entries if e.get("sentiment") == "negative")
        negative_pct = round(100 * negative / total) if total else 0

        groups = {}
        for e in entries:
            issue = e.get("issue") or e.get("summary") or ""
            name = normalize_category(e.get("category") or "", issue)
            group = groups.setdefault(name, {"category": name, "count": 0, "examples": []})
            group["count"] += 1
            if issue and issue not in group["examples"] and len(group["examples"]) < 3:
                group["examples"].append(issue)

        group_list = sorted(groups.values(), key=lambda g: g["count"], reverse=True)

        return jsonify({
            "success": True,
            "total": total,
            "issues_detected": len(group_list),
            "negative_pct": negative_pct,
            "groups": group_list,
        })

    except Exception as e:
        print("INSIGHTS ERROR:", repr(e))
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    app.run(debug=os.getenv("FLASK_DEBUG") == "1")