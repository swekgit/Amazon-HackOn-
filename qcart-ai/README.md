# 🛒 QCart AI — *say your moment, get your cart*

Moment-aware quick commerce. Delivery is already 10 minutes — but building the
cart still takes 30–40. QCart AI removes that: describe (or speak) the moment —
"movie night for 4", "I have fever", "party for 6" — and Claude builds a complete,
checkout-ready cart in seconds. Then you just **talk to it** to refine.

> Thesis: *shift commerce from customer-aware to moment-aware.*

## Folder structure (split by developer)

```
qcart-ai/
├── backend/                         ▶ DEV 1 (the brain)
│   ├── main.py        FastAPI · POST /api/cart  (ties everything together)
│   ├── brain.py       Claude call · prompt · PROMPT CACHING
│   ├── gap.py         Gap Engine (free-delivery filler, deterministic)
│   ├── cache.py       Response cache (in-memory, TTL)
│   ├── catalog.py     Catalog + history loader + helpers
│   ├── data/
│   │   ├── products.json   catalog (~55 items)
│   │   └── orders.json     seeded history + prefs  (Context Engine)
│   ├── requirements.txt
│   └── .env.example
└── frontend/
    └── src/
        ├── App.jsx                  ▶ DEV 2  (layout, wires all)
        ├── api/
        │   ├── client.js            ▶ DEV 2  (real API, USE_MOCK flag)
        │   └── mock.js              ▶ DEV 2  (mirrors the contract)
        ├── state/useConversation.js ▶ DEV 2  (conversation + cart state)
        ├── components/
        │   ├── ChatThread.jsx       ▶ DEV 2
        │   ├── CartPanel.jsx        ▶ DEV 2
        │   ├── CartItem.jsx         ▶ DEV 2
        │   ├── Composer.jsx         ▶ DEV 3  (input + send)
        │   ├── VoiceButton.jsx      ▶ DEV 3  (speech-to-text)
        │   ├── MissionTiles.jsx     ▶ DEV 3
        │   ├── GapNudge.jsx         ▶ DEV 3
        │   └── SavedCounter.jsx     ▶ DEV 3  (time/taps saved)
        ├── lib/   format.js, theme.js (urgency theming) ▶ DEV 3
        └── data/missions.js         ▶ DEV 3
```

## The API contract (lock this first — it unblocks all 3 devs)

`POST /api/cart`  →  request `{ "message": "...", "cart": [...] }`
```json
{
  "reply": "Movie night for 4 — snacks, drinks & something sweet.",
  "context": "movie_night",
  "urgency": "normal",
  "cart": [ { "id":"p001","name":"Butter Popcorn","price":65,"quantity":2,"reason":"movie staple","line_total":130 } ],
  "suggestions": [ { "id":"p005","name":"Dark Chocolate","price":110,"reason":"something sweet" } ],
  "subtotal": 430,
  "free_delivery_threshold": 199,
  "gap_amount": 0,
  "gap_fillers": [],
  "cached": false
}
```

## Caching (two layers)
1. **Prompt caching** (`brain.py`) — the catalog + history block is marked
   `cache_control: ephemeral`, so Claude caches that prefix and only re-reads the
   small dynamic part (cart + message). Cheaper + faster across a session.
2. **Response cache** (`cache.py`) — identical `(message + cart state)` returns
   instantly from memory (10-min TTL). Great for repeated demo prompts. Swap the
   dict for Redis to scale; same interface.

## Run it (2 terminals)
```bash
# backend
cd backend && python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # paste your key from console.anthropic.com
uvicorn main:app --reload --port 8000

# frontend
cd frontend && npm install && npm run dev
```
Then set `USE_MOCK = false` in `src/api/client.js` to hit the real backend.
Vite proxies `/api` → :8000. Use `CLAUDE_MODEL=claude-haiku-4-5-20251001` in `.env` for a snappier demo.

## Demo arc (~90 sec)
1. Tap / say **"Movie night for 4"** → cart + reasons + "saved 22 min, 32 taps".
2. Type **"make it premium"** → cart upgrades live (conversational).
3. On a small order, **Gap nudge**: "₹X to free delivery → add this" → one tap.
4. **"I have fever"** → Care mode (rose theme), essentials first.
5. One-tap checkout → "arriving in 10 min".
