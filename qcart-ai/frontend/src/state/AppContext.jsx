import { createContext, useContext, useState, useMemo, useCallback } from "react";
import { sendTurn } from "../api/client.js";
import { useTheme } from "./useTheme.js";
import { ORDER_HISTORY } from "../data/orders.js";

const AppCtx = createContext(null);

export function AppProvider({ children }) {
  const [messages, setMessages] = useState([]);
  const [cart, setCart] = useState([]);
  const [meta, setMeta] = useState({
    context: "routine",
    urgency: "normal",
    threshold: 199,
    gapFillers: [],
    suggestions: [],
    buildTime: null,
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [cartOpen, setCartOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);

  const themeState = useTheme();

  const subtotal = useMemo(
    () => cart.reduce((s, i) => s + i.price * i.quantity, 0),
    [cart]
  );
  const gapAmount = Math.max(0, meta.threshold - subtotal);

  const send = useCallback(
    async (text) => {
      const value = (text || "").trim();
      if (!value || loading) return;
      setMessages((m) => [...m, { role: "user", text: value }]);
      setLoading(true);
      setError("");
      // Detect theme from user input
      themeState.setThemeByContext(value);
      const startTime = performance.now();
      try {
        const res = await sendTurn({ message: value, cart });
        const buildTime = ((performance.now() - startTime) / 1000).toFixed(1);
        setCart(res.cart);
        setMeta({
          context: res.context,
          urgency: res.urgency,
          threshold: res.free_delivery_threshold,
          gapFillers: res.gap_fillers || [],
          suggestions: res.suggestions || [],
          buildTime,
        });
        setMessages((m) => [...m, { role: "assistant", text: res.reply }]);
        // Auto-open cart on first build
        if (res.cart.length > 0) setCartOpen(true);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    },
    [loading, cart, themeState]
  );

  const setQty = useCallback(
    (id, qty) =>
      setCart((c) =>
        qty <= 0
          ? c.filter((i) => i.id !== id)
          : c.map((i) =>
              i.id === id ? { ...i, quantity: qty, line_total: i.price * qty } : i
            )
      ),
    []
  );

  const removeItem = useCallback(
    (id) => setCart((c) => c.filter((i) => i.id !== id)),
    []
  );

  const addProduct = useCallback(
    (p) =>
      setCart((c) =>
        c.some((i) => i.id === p.id)
          ? c
          : [...c, { ...p, quantity: 1, reason: p.reason || "", line_total: p.price }]
      ),
    []
  );

  const clearCart = useCallback(() => setCart([]), []);

  const value = useMemo(
    () => ({
      // Cart
      cart,
      addProduct,
      removeItem,
      setQty,
      subtotal,
      clearCart,
      hasCart: cart.length > 0,
      // Conversation
      messages,
      send,
      loading,
      error,
      // Theme
      theme: themeState.currentTheme,
      themeName: themeState.themeName,
      setThemeByContext: themeState.setThemeByContext,
      isNightMode: themeState.isNightMode,
      // UI
      cartOpen,
      setCartOpen,
      chatOpen,
      setChatOpen,
      // Meta
      meta,
      gapAmount,
      // Data
      orderHistory: ORDER_HISTORY,
    }),
    [
      cart, addProduct, removeItem, setQty, subtotal, clearCart,
      messages, send, loading, error,
      themeState, cartOpen, chatOpen, meta, gapAmount,
    ]
  );

  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>;
}

export function useApp() {
  const ctx = useContext(AppCtx);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
