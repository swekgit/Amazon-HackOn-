import { mockTurn } from "./mock.js";

// Flip to false once the backend is ready. Lets frontend work fully standalone.
const USE_MOCK = false;

export async function sendTurn({ message, cart }) {
  if (!USE_MOCK) return mockTurn({ message, cart });

  const res = await fetch("/api/cart", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, cart }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail || "Something went wrong. Try again.");
  }
  return res.json();
}
