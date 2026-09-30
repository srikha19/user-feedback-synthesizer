# User Feedback Synthesizer

An AI agent that remembers customer feedback across channels and weeks using [Hindsight](https://github.com/vectorize-io/hindsight) memory, then answers questions like *"Did our search fix work?"* with real customer names, dates, and trends.

Most feedback tools show you a pile of comments. This one remembers **what customers said and what you changed**, so it can tell you whether a change actually helped.

## The problem

Product teams collect feedback from many places: app reviews, support tickets, sales calls, emails, and surveys. The information is scattered, and nobody remembers which complaint came before or after a release. An assistant with no memory can only give generic advice.

## What it does

- **Add Feedback:** choose a channel, enter a customer name and their feedback. An LLM (Groq) extracts the main issue, category, and sentiment, and the full record is stored in Hindsight.
- **Log product changes:** the "Product Update" channel stores a release (for example, "Shipped faster search") as a dated memory next to the feedback, so the agent can compare before and after.
- **Feedback Chat:** ask questions in plain English. Every question is answered twice, **without memory** (a generic LLM answer) and **with Hindsight memory**, with the recalled memories shown underneath.
- **Insights:** a summary of stored feedback, grouped issue categories, and negative sentiment.

## How Hindsight memory is used

Memory is the core of the project, not an add-on.

| Operation | Where | What it does |
|-----------|-------|--------------|
| `retain` | `POST /analyze` | Stores each customer feedback (with customer, channel, date, original text, and AI analysis) and each product change as a memory in the bank `feedback-demo-v2`. |
| `recall` | `POST /ask` | Retrieves the memories most relevant to the user's question. They are passed to the LLM as context and displayed in the UI. |

Design decisions:

- **Product changes are memories too.** This is what lets the agent answer "did the fix work?" and "what new problems appeared after our latest release?".
- **Dates and channels are written into each memory.** The model can reason about order (before and after) and about where feedback came from.
- **Recency rules in the answer prompt.** When a customer has several memories, the latest one is treated as their current status.
- **A fresh async Hindsight client per call**, run with `asyncio.run(...)`, to avoid event-loop errors inside Flask routes.

## Before and after

Question: *"Did the search fix work?"*

| Without memory | With Hindsight memory |
|----------------|----------------------|
| Generic advice about tracking click-through rate, error logs, and metrics. | Names customers who reported the slow search, notes they said it improved after the 18 Sept update, and links this to the change that cut search time from 8 seconds to under 1 second. |

Adding one new support ticket changes the next answer with no code changes, because the new memory is recalled.

## Tech stack

- **Backend:** Python, Flask
- **Memory:** Hindsight (`hindsight-client`)
- **LLM:** Groq, model `openai/gpt-oss-120b`
- **Frontend:** HTML, CSS, and vanilla JavaScript

## Project structure

```
user-feedback-synthesizer/
├── app.py              # Flask app: /analyze, /ask, /insights
├── seed.py             # Loads sample feedback and a product update
├── templates/
│   └── index.html      # UI: Add Feedback, Feedback Chat, Insights
├── static/
│   └── style.css
├── requirements.txt
├── .env.example        # Template for your API keys
└── .gitignore
```

## Setup

### 1. Clone and install

```bash
git clone https://github.com/YOUR_USERNAME/user-feedback-synthesizer.git
cd user-feedback-synthesizer

python -m venv venv
```

Activate the virtual environment:

```bash
# Windows (PowerShell)
venv\Scripts\Activate.ps1

# macOS / Linux
source venv/bin/activate
```

Then install the dependencies:

```bash
pip install -r requirements.txt
```

### 2. Add your API keys

Copy `.env.example` to `.env` and fill in your keys:

```
GROQ_API_KEY=your_groq_api_key_here
HINDSIGHT_API_KEY=your_hindsight_api_key_here
HINDSIGHT_API_URL=https://api.hindsight.vectorize.io
```

- Groq key: <https://groq.com/>
- Hindsight Cloud: <https://ui.hindsight.vectorize.io> (or run the [open-source version](https://github.com/vectorize-io/hindsight))

### 3. Run the app

```bash
python app.py
```

Open <http://127.0.0.1:5000> in your browser.

### 4. Load the sample data (optional, run once)

With the app running, open a second terminal in the project folder:

```bash
python seed.py
```

This sends 17 sample items to the app: customer feedback across five channels dated from 25 Aug to 28 Sept 2026, plus a product update on 18 Sept. Run it **only once** to avoid duplicates. Hindsight processes memories in the background, so wait a couple of minutes before asking questions.

## Try it

Ask these in the **Feedback Chat** tab:

1. `What are customers saying about search, and did our search update help?`
2. `What new problems appeared after our latest product change?`
3. `What are the most common customer complaints across all channels?`

Then add a new support ticket in **Add Feedback** (for example, a customer reporting that UPI payments are still failing), wait a minute, and ask question 2 again to see the answer update.

## API endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/` | Web UI |
| POST | `/analyze` | Body: `customer`, `feedback`, `channel`, optional `date`. Analyzes feedback, or records a product change, and stores it in Hindsight. |
| POST | `/ask` | Body: `question`. Returns the answer without memory, the answer with Hindsight memory, and the recalled memories. |
| GET | `/insights` | Returns totals, negative sentiment percentage, and grouped issue categories. |

## Known limitations

- **Insights uses a local file.** The chat answers come from Hindsight, but the Insights counts are read from a local `feedback_log.json`. Deriving them from Hindsight is a natural next step.
- **Sample data is synthetic.** The seed data is written to resemble real feedback. It shows how the memory behaves, not performance at real customer volume.
- **Answers depend on the LLM.** Recency rules are enforced through the prompt, so an answer can occasionally weigh an older memory too heavily.
- **Memory processing is not instant.** Newly stored items can take a minute or two to appear in answers.
- **Development server.** The app runs with Flask's built-in server and is not production hardened.

## Roadmap

- Derive Insights directly from Hindsight memories
- Sentiment trends over time
- Import feedback from real channels (support desk, app store, CRM)
- Per-customer history view

## Team

- MY NAME : srikha kommineni
- TEAMMATE NAMES : sri durga raavi,kundanasahithi maddala,nikhath parveen shaik,sri vyshnavi
