import { useMemo, useState } from "react";
import { sendTurn } from "../api/client.js";

// Single source of truth for the conversation + live cart.
export function useConversation({ customerId, city } = {}) {
  const [messages, setMessages] = useState([]); // {role:'user'|'assistant', text}
  const [cart, setCart] = useState([]);
  const [meta, setMeta] = useState({
    context: "routine",
    urgency: "normal",
    threshold: 199,
    gapFillers: [],
    suggestions: [],
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // Live totals (recompute on every local edit, not just server turns).
  const subtotal = useMemo(
    () => cart.reduce((s, i) => s + i.price * i.quantity, 0),
    [cart]
  );
  const gapAmount = Math.max(0, meta.threshold - subtotal);

  async function send(text) {
    const value = (text || "").trim();
    if (!value || loading) return;
    setMessages((m) => [...m, { role: "user", text: value }]);
    setLoading(true);
    setError("");
    try {
      const res = await sendTurn({ message: value, cart, customerId, city });
      setCart(res.cart);
      setMeta({
        context: res.context,
        urgency: res.urgency,
        threshold: res.free_delivery_threshold,
        gapFillers: res.gap_fillers || [],
        suggestions: res.suggestions || [],
      });
      setMessages((m) => [...m, { role: "assistant", text: res.reply }]);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }

  const setQty = (id, qty) =>
    setCart((c) =>
      qty <= 0
        ? c.filter((i) => i.id !== id)
        : c.map((i) => (i.id === id ? { ...i, quantity: qty, line_total: i.price * qty } : i))
    );

  const removeItem = (id) => setCart((c) => c.filter((i) => i.id !== id));

  const addProduct = (p) =>
    setCart((c) =>
      c.some((i) => i.id === p.id)
        ? c
        : [...c, { ...p, quantity: 1, reason: p.reason || "", line_total: p.price }]
    );

  return {
    messages, cart, meta, loading, error,
    subtotal, gapAmount,
    send, setQty, removeItem, addProduct,
    hasCart: cart.length > 0,
  };
}
