import os
from dotenv import load_dotenv
from groq import Groq
from hindsight_client import Hindsight

load_dotenv()

# -----------------------------
# Configuration
# -----------------------------

BANK_ID = "feedback-demo-v2"

groq_client = Groq(
    api_key=os.getenv("GROQ_API_KEY")
)

hindsight_client = Hindsight(
    base_url=os.getenv("HINDSIGHT_API_URL"),
    api_key=os.getenv("HINDSIGHT_API_KEY")
)


# -----------------------------
# Test customer feedback
# -----------------------------

customer = "Rahul"
feedback = "The product search is very slow. It takes too long to find products."


# -----------------------------
# Ask Groq to analyze it
# -----------------------------

response = groq_client.chat.completions.create(
    model="openai/gpt-oss-120b",
    messages=[
        {
            "role": "system",
            "content": """
You are a customer feedback analysis agent.

Analyze the customer feedback and identify:

1. Main issue
2. Category
3. Sentiment
4. Short summary

Keep the answer concise.
"""
        },
        {
            "role": "user",
            "content": f"""
Customer: {customer}

Feedback:
{feedback}
"""
        }
    ]
)

analysis = response.choices[0].message.content

print("\n===== GROQ ANALYSIS =====")
print(analysis)


# -----------------------------
# Store the memory in Hindsight
# -----------------------------

memory = f"""
Customer: {customer}

Original feedback:
{feedback}

AI analysis:
{analysis}
"""

hindsight_client.retain(
    bank_id=BANK_ID,
    content=memory
)

print("\n===== HINDSIGHT =====")
print("Customer feedback successfully stored!")