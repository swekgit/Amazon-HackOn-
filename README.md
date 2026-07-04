<p align="center">
  <img src="https://img.shields.io/badge/Amazon-HackOn-FF9900?style=for-the-badge&logo=amazon&logoColor=white" alt="Amazon HackOn"/>
  <img src="https://img.shields.io/badge/AWS-Bedrock-232F3E?style=for-the-badge&logo=amazonaws&logoColor=white" alt="AWS Bedrock"/>
  <img src="https://img.shields.io/badge/AWS-OpenSearch-005EB8?style=for-the-badge&logo=amazonaws&logoColor=white" alt="AWS OpenSearch"/>
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=for-the-badge&logo=react&logoColor=black" alt="React"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/MongoDB-Atlas-47A248?style=for-the-badge&logo=mongodb&logoColor=white" alt="MongoDB"/>
</p>

<h1 align="center">🛒 QCart AI — Moment-Aware Quick-Commerce Cart Assistant</h1>

<p align="center">
  <strong>Say your moment, get your cart.</strong><br/>
  An AI-powered conversational shopping experience that turns a single sentence into a complete,
  personalized, ready-to-checkout cart on quick-commerce platforms.
</p>

<p align="center">
  <a href="#the-problem">Problem</a> •
  <a href="#our-vision">Vision</a> •
  <a href="#solution-overview">Solution</a> •
  <a href="#key-features">Features</a> •
  <a href="#technical-architecture">Architecture</a> •
  <a href="#engineering-principles">Engineering</a> •
  <a href="#getting-started">Setup</a> •
  <a href="#whats-next">Roadmap</a>
</p>

---

## The Problem

Quick-commerce delivers in 10 minutes — but building the cart still takes **30–40 minutes** of
searching, scrolling, comparing, and second-guessing whether you forgot something.

| Pain Point | Impact |
|---|---|
| **Search fatigue** | Users type, scroll, and tap through dozens of products to build one list |
| **No contextual understanding** | Platforms don't understand *why* you're shopping — a movie night needs popcorn, drinks, and snacks *together* |
| **Zero personalization at cart level** | Recommendations live on product pages; carts are dumb containers |
| **Missed upsell moments** | Free-delivery thresholds go unfilled; better alternatives are never surfaced |
| **Repetitive reordering** | Users manually rebuild the same weekly groceries, care kits, or party baskets every time |

> The experience feels transactional instead of assistive. QCart AI makes cart-building effortless.

---

## Our Vision

**From customer-aware to moment-aware.**

Today's platforms know *who* you are. QCart understands the *moment* you're in — a party, a fever,
a recipe, a monthly restock — and assembles the whole cart around it. What if building a cart was as
easy as telling a friend what you need?

QCart AI is a **conversational, context-aware, and deeply personalized** experience powered by
Amazon Bedrock foundation models, semantic vector retrieval, and a multi-layered intelligence stack.

---

## Solution Overview

```
"Movie night for 4"                  ->  Complete cart in seconds (popcorn, chips, drinks)
"Gajar ka halwa for 4, ghee already" ->  Recipe broken into ingredients; only what's missing added
"I have fever"                       ->  Urgency-tagged care essentials, pre-prioritized
"Make it cheaper"                    ->  Price-aware swaps within the same product group
```

### What Makes Us Different

| Dimension | Traditional Apps | QCart AI |
|---|---|---|
| Cart building | Manual search + add | One sentence = full cart |
| Recipes | Search each ingredient | State the dish -> ingredients resolved & scaled |
| Refinement | Delete -> research -> re-add | "Make it cheaper" / "Remove dairy" |
| Personalization | Product-level recs | Cart-level, segment + behavior driven |
| Context awareness | None | Understands occasions, urgency, household patterns |
| Reorder | "Buy again" button | Cycle-aware predictions, before you run out |

---

## Key Features

### 1. Conversational Moment Cart
Natural language (typed or voice) -> structured, ready-to-checkout cart in one turn.
- **Occasion:** "Movie night for 4", "Party for 10"
- **Need:** "I have fever", "Baby essentials"
- **Routine:** "Weekly groceries", "Restock staples"

### 2. Recipe-to-Cart
State a dish and QCart does the rest:
> **"Gajar ka halwa for 4, ghee already hai"** -> detects the dish, servings, and what you *already
> have* -> breaks it into ingredients -> maps each to a **real catalog product** -> adds only what's
> **missing** (carrot, sugar, milk, khoya...) and **skips** the ghee you already own.

Powered by Bedrock (Nova Lite for detection) + semantic retrieval for accurate, category-aware
ingredient -> product resolution (no "sugar -> cola" mismatches).

### 3. Outcome Assurance — Readiness
For goal-oriented carts, a live **readiness meter** shows how ready the cart is for the moment:
- Bands: *Just started -> Almost there -> Good to go -> "Movie-night ready ✓"*
- Shows exactly **what's missing** ("You're missing: dip, plates")
- Turns green with a small celebration at 100%

### 4. Alternatives Widget
For each cart item, one-tap swaps from the same product group:
- **Cheaper** — a lower-priced option in the same group
- **Faster** — a Prime-eligible option
- Shows brand + price; only appears when real alternatives exist

### 5. Segment-Based Personalization
No cold start. Every customer is understood via **segment + behavioral tags + city + time-of-day**:
- Segments: **student / working professional / senior / family**
- e.g. Ananya -> coffee & premium breakfast; Ravi -> household staples; Meera -> healthy family picks
- Deterministic, explainable re-ranking (no LLM in the hot path) -> fast and testable

### 6. Predictive Replenishment
Cycle-aware reorder suggestions before you run out:
> Meera -> **Period-care kit** (due in 2 days) · Ravi -> **Monthly staples** — one-tap reorder

### 7. Free-Delivery Gap Intelligence
Not a static banner — a smart nudge that computes the exact gap to free delivery (₹399) and suggests
**context-relevant** fillers to close it.

### 8. Cart-Aware Payment & Offers
Surfaces the best applicable offers for the current cart ("add ₹X more to unlock 10% off") plus
saved payment methods — a frictionless checkout moment. *(Offers are demo/mock data.)*

### 9. City-Level Trending & Voice
MongoDB-backed trending per city, and English voice input (Web Speech API) so you can *speak* your
moment.

---

## Technical Architecture

```
+-----------------------------------------------------------------------+
|                    FRONTEND — React + Vite + Tailwind                 |
|   Conversational UI · For You feed · Cart drawer · Readiness · Voice  |
+-----------------------------------+-----------------------------------+
                                    |  HTTPS / REST
+-----------------------------------v-----------------------------------+
|                      API LAYER — FastAPI (Python)                     |
|                                                                       |
|   +-------------+   +------------------+   +----------------------+   |
|   | AI / Brain  |   | Retrieval (RAG)  |   | Personalization      |   |
|   | Bedrock     |   | Amazon Titan     |   | Engine (rules):      |   |
|   | Nova Pro    |<->| embeddings +     |   | segment + tags +     |   |
|   | (cart) +    |   | vector kNN over  |   | city + time          |   |
|   | Nova Lite   |   | 1000 SKUs        |   | (deterministic)      |   |
|   +-------------+   +--------+---------+   +----------+-----------+   |
|         |                    |                        |               |
|   +-----v--------+   +-------v--------+   +------------v-----------+  |
|   | Gap Engine   |   | Response Cache |   | Model Router           |  |
|   | (readiness / |   | (in-memory,    |   | (region-aware,         |  |
|   | free-deliv.) |   | SHA-256 keyed) |   | multi-model failover)  |  |
|   +--------------+   +----------------+   +------------------------+  |
+-----------------------------------+-----------------------------------+
                                    |
      +-----------------------------+-----------------------------+
      v                             v                             v
+-------------+          +------------------+          +-----------------+
| MongoDB     |          |  Amazon Bedrock  |          |   Amazon S3     |
| Atlas       |          |  Nova Pro /      |          |  product images |
| catalog ·   |          |  Nova Lite ·     |          |                 |
| customers · |          |  Titan Embed v2  |          |                 |
| tags ·      |          |                  |          |                 |
| cycles ·    |          |                  |          |                 |
| trending    |          |                  |          |                 |
+-------------+          +------------------+          +-----------------+

  - - - production / scale layer (roadmap) - - -
  Redis (ElastiCache) · scheduled knowledge-refresh (CRON/EventBridge) ·
  ALB + ACM · Cognito · API Gateway · ECS Fargate auto-scaling
```

### Intelligence Stack

| Layer | Component | Role | Approach |
|---|---|---|---|
| **Reasoning** | Brain (Bedrock) | Understands intent, builds & refines carts, classifies context/urgency | Amazon Bedrock — Nova Pro / Nova Lite |
| **Retrieval** | RAG | Embeds the query, retrieves the most relevant real products, grounds the LLM | Amazon Titan Text Embeddings v2 + vector kNN |
| **Recipe** | Ingredient Resolver | Maps dish -> scaled, category-correct catalog products; skips "already have" | Bedrock + embedding-based resolver |
| **Personalization** | Recommendation Engine | Ranks by segment + tags + city + time | Deterministic rules (no LLM) |
| **Optimization** | Gap Engine | Cart readiness + free-delivery fillers | Deterministic |
| **Prediction** | Cycle Engine | Predicts reorder timing from purchase intervals | Deterministic |

### Grounded Retrieval (RAG)

Every product query is embedded with **Amazon Titan Text Embeddings v2 (1024-dim)** and matched
against the pre-embedded catalog via **vector kNN** — so the LLM only ever sees *real* products and
picks from those. This keeps responses **grounded (no hallucinated SKUs)**, low-latency, and precise
(e.g. "sugar" resolves to an actual staples product, not a soft drink). The embedding index was
built with **Amazon OpenSearch**; query-time retrieval runs in-process for speed, with a keyword
fallback for resilience.

### Model Router — Multi-Model Failover

- **Task-aware routing** — heavy reasoning -> Nova Pro; lightweight detection/classification -> Nova Lite
- **Automatic failover** across models so a throttle/outage never hard-fails a user
- **Region-aware** routing and **latency logging** on every call

---

## Engineering Principles

### 1. AI where it matters, deterministic everywhere else
Cart reasoning and recipe understanding use LLMs; **personalization, gap-filling, and cycle
prediction are pure rules/math** — fast (0 ms vs seconds), testable, explainable, and cost-free.

### 2. Grounded, hallucination-safe output
Every product ID returned by the LLM is validated against the real catalog; invalid IDs are dropped.
Retrieval only surfaces real SKUs. **No hallucinated products ever reach the user.**

### 3. Graceful degradation
| Failure | Handling |
|---|---|
| Model throttled/down | Automatic fallback to the next model |
| Vector retrieval unavailable | Falls back to keyword retrieval — never crashes the cart |
| MongoDB unreachable | Falls back to a bundled catalog snapshot |
| Malformed LLM JSON | Regex extraction fallback before failing |
| Empty/invalid cart | Helpful "try rephrasing" message, never hallucinated data |

### 4. Caching for demo-speed & cost
Identical requests are served from an in-memory, SHA-256-keyed cache in <1 ms; a warm-up pass
pre-fills common scenarios. *(Redis is the planned production caching layer for shared,
cross-instance caching.)*

### 5. Observability
Every model call is logged with model, region, latency, token counts, and fallback events for
real-time cost/performance monitoring.

---

## Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | React 18 + Vite + Tailwind CSS |
| **Backend** | FastAPI (Python) |
| **AI / LLM** | Amazon Bedrock — Nova Pro + Nova Lite |
| **Retrieval** | Amazon Titan Text Embeddings v2 + vector kNN (index built on Amazon OpenSearch) |
| **Database** | MongoDB Atlas |
| **Media** | Amazon S3 (product images) |
| **Deployment** | Docker + Nginx on AWS EC2 |

---

## Getting Started

### Prerequisites
- Python 3.11+ · Node.js 18+
- AWS credentials with Bedrock access (Nova Pro, Nova Lite, Titan Embeddings v2)
- MongoDB Atlas URI

### Backend

```bash
cd qcart-ai/backend

python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

cp .env.example .env
# Edit .env: MONGODB_URI, AWS credentials/region, Bedrock + retrieval config

python seed_catalog.py          # seed the 1000-product catalog into MongoDB

uvicorn main:app --reload --port 8000
```

### Frontend

```bash
cd qcart-ai/frontend
npm install
npm run dev                          # dev
# npm run build && npm run preview   # production build (use for demos)
```

> **Note:** Voice input uses the browser Web Speech API, which requires a secure context — use
> `localhost` or an HTTPS URL for the microphone to work.

---

## Demo Scenarios

| Scenario | What It Shows |
|---|---|
| `"Movie night for 4"` | Context detection, occasion-aware cart, readiness meter |
| `"Gajar ka halwa for 4, ghee already hai"` | Recipe -> scaled ingredients, "already have" skipped |
| `"I need milk and atta"` | Alternatives widget (cheaper / faster swaps) |
| `"I have fever"` | Urgency classification, health-context cart |
| **For You** (Ananya / Ravi / Meera) | Segment + tag driven personalization, per-user recs |
| **Predicted reorders** | Meera's period-care kit · Ravi's monthly staples |
| **Cart page** | Free-delivery gap + cart-aware payment offers |

---

## What's Next

Each future capability already has a home in our architecture:

- **Failure Memory Engine** — learn from returns / out-of-stock / forgotten items so the same
  mistake never repeats *(S3 data lake -> SageMaker)*.
- **Resume / Funnel Rescue** — pick an abandoned moment back up: "your movie-night cart is here —
  one tap to finish" *(DynamoDB + EventBridge -> SNS nudge)*.
- **Predictive Moments** — predict the *next* moment ("Friday 7 PM -> movie night") and pre-stage the
  cart *(SageMaker forecasting)*.
- **MomentOS across categories** — the same moment engine extends to pharmacy, home, events, and
  gifting: one intent-to-fulfillment layer on top of the whole catalog.
- **Multi-language moments + Alexa** — state your moment in any Indian language, or through Alexa
  *(Bedrock multilingual + Transcribe/Polly)*.
- **Production scale** — Redis caching, scheduled knowledge-refresh (CRON/EventBridge re-computing
  customer tags/segments from recent behavior), ALB + ACM, Cognito auth, API Gateway, and ECS
  auto-scaling.

---

## Project Structure

```
qcart-ai/
├── backend/
│   ├── main.py                  # FastAPI app + endpoints
│   ├── brain.py                 # LLM reasoning: cart, recipe detection & extraction
│   ├── model_router.py          # Multi-model Bedrock router with failover
│   ├── catalog.py               # Catalog access, vector retrieval, ingredient resolver, alternatives
│   ├── recommendation_engine.py # Segment + tags + city + time recommendations
│   ├── persona.py               # Customer segments + inference logic
│   ├── gap.py                   # Free-delivery gap intelligence
│   ├── cache.py                 # In-memory response cache (TTL)
│   ├── db.py                    # MongoDB Atlas connection layer
│   ├── seed_catalog.py          # Seed the 1000-product catalog
│   └── data/
│       ├── products.json        # Catalog fallback snapshot
│       └── orders.json          # User history for personalization
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── components/          # Chat, Cart, ForYou, Readiness, Recipe, Voice...
│   │   ├── state/               # AppContext + hooks
│   │   └── api/                 # Backend client
│   └── package.json
└── README.md
```

---

## Team HACK PINK

Built with love for **Amazon HackOn 6.0**

---

## License

Built as a hackathon submission. All rights reserved.