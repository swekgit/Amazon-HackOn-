import { createContext, useContext, useState, useMemo, useCallback, useEffect } from "react";
import { sendTurn, fetchCities, fetchTrending, fetchMomentCart } from "../api/client.js";
import { computePaymentOffers } from "../lib/paymentOffers.js";
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
  readiness: null,
  buildTime: null,
  recipe: null,
  paymentOffers: [],
  savedPayments: [],
  query: "",
  momentLabel: "",
});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [cartOpen, setCartOpen] = useState(false);
  const [chatOpen, setChatOpen] = useState(false);

  // ── City & Trending state ──────────────────────────────────────────────────
  const [city, setCityRaw] = useState("Bangalore");
  const [cities, setCities] = useState([]);
  const [trendingProducts, setTrendingProducts] = useState([]);
  const [trendingLoading, setTrendingLoading] = useState(false);

  const [customerId, setCustomerId] = useState("cust_ananya");
  const [customerProfile, setCustomerProfile] = useState({
    segment: "working",
    tags: [],
  });

  const themeState = useTheme();

  const subtotal = useMemo(
    () => cart.reduce((s, i) => s + i.price * i.quantity, 0),
    [cart]
  );
  const gapAmount = Math.max(0, meta.threshold - subtotal);

  const readiness = useMemo(() => {
  const raw = meta.readiness;

  if (!raw?.essentials?.length) {
    return null;
  }

  const satisfiedIds = new Set();
  for (const item of cart) {
    satisfiedIds.add(item.id);
    for (const id of item.satisfiesEssentials || []) {
      satisfiedIds.add(id);
    }
  }

  const present = raw.essentials.filter((e) =>
    satisfiedIds.has(e.id)
  );

  const missing = raw.essentials.filter((e) =>
    !satisfiedIds.has(e.id)
  );

  const score = Math.round(
    (present.length / raw.essentials.length) * 100
  );

  const momentName = (() => {
    if (meta.momentLabel) return meta.momentLabel.toLowerCase();
    const fromLabel = raw.label?.replace(/\s*readiness\s*$/i, "").trim();
    if (fromLabel) return fromLabel.toLowerCase();
    if (meta.context && !["routine", "other"].includes(meta.context)) {
      return meta.context.replace(/_/g, " ").toLowerCase();
    }
    return "your moment";
  })();

  const phrase = score >= 100
    ? `you are all set for ${momentName}`
    : score >= 71
    ? `good to go for ${momentName}`
    : score >= 41
    ? `almost ready for ${momentName}`
    : `missing out on ${momentName}`;

  return {
    label: raw.label,
    momentName,
    phrase,
    essentials: raw.essentials,
    present,
    missing,
    score,
    complete:
      present.length === raw.essentials.length,
  };
}, [meta.readiness, meta.momentLabel, meta.context, cart]);

  const paymentOffers = useMemo(() => {
    const fillerPool = [...(meta.suggestions || []), ...(meta.gapFillers || [])];
    return computePaymentOffers(cart, subtotal, meta.context, fillerPool);
  }, [cart, subtotal, meta.context, meta.suggestions, meta.gapFillers]);

  const applyCartResponse = useCallback((res, queryText, buildTime, momentLabel) => {
    setCart(res.cart);
    setMeta({
      context: res.context,
      urgency: res.urgency,
      threshold: res.free_delivery_threshold,
      gapFillers: res.gap_fillers || [],
      suggestions: res.suggestions || [],
      readiness: res.readiness || null,
      buildTime,
      recipe: res.recipe || null,
      paymentOffers: res.payment_offers || [],
      savedPayments: res.saved_payments || [],
      query: queryText,
      momentLabel: momentLabel || "",
    });
    setMessages((m) => [...m, { role: "assistant", text: res.reply }]);
    if (res.cart.length > 0) setCartOpen(true);
  }, []);

  const send = useCallback(
    async (text) => {
      const value = (text || "").trim();
      if (!value || loading) return;
      setMessages((m) => [...m, { role: "user", text: value }]);
      setLoading(true);
      setError("");
      themeState.setThemeByContext(value);
      const startTime = performance.now();
      try {
        const res = await sendTurn({
          message: value,
          cart,
          customerId,
          city,
        });
        const buildTime = ((performance.now() - startTime) / 1000).toFixed(1);
        applyCartResponse(res, value, buildTime);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    },
    [loading, cart, themeState, customerId, city, applyCartResponse]
  );

  const sendMoment = useCallback(
    async (moment) => {
      if (!moment?.id || loading) return;
      const queryText = moment.intent || moment.label;
      const displayLabel = moment.label || "";
      setMessages((m) => [...m, { role: "user", text: queryText }]);
      setLoading(true);
      setError("");
      themeState.setThemeByContext(queryText);
      const startTime = performance.now();
      try {
        const res = await fetchMomentCart(moment.id, customerId, city);
        const buildTime = ((performance.now() - startTime) / 1000).toFixed(1);
        applyCartResponse(res, queryText, buildTime, displayLabel);
      } catch (e) {
        try {
          const res = await sendTurn({
            message: queryText,
            cart: [],
            customerId,
            city,
          });
          const buildTime = ((performance.now() - startTime) / 1000).toFixed(1);
          applyCartResponse(res, queryText, buildTime, displayLabel);
        } catch (fallbackErr) {
          setError(fallbackErr.message || e.message);
        }
      } finally {
        setLoading(false);
      }
    },
    [loading, customerId, city, themeState, applyCartResponse]
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
const swapItem = useCallback((oldId, newProduct) => {
  setCart((current) =>
    current.map((item) => {
      if (item.id !== oldId) return item;

      return {
        ...newProduct,
        quantity: item.quantity,
        reason: newProduct.reason || item.reason || "",
        line_total: newProduct.price * item.quantity,
        satisfiesEssentials: item.satisfiesEssentials ?? [item.id],
      };
    })
  );
}, []);

  const addProduct = useCallback(
    (p) =>
      setCart((c) =>
        c.some((i) => i.id === p.id)
          ? c
          : [...c, { ...p, quantity: 1, reason: p.reason || "", line_total: p.price }]
      ),
    []
  );

  const clearCart = useCallback(() => {
    setCart([]);
    setMeta((prev) => ({ ...prev, suggestions: [], gapFillers: [], readiness: null, momentLabel: "" }));
  }, []);

  // ── City selection & trending fetch ─────────────────────────────────────────

 const loadTrending = useCallback(async (targetCity) => {
  console.log("loadTrending fired:", targetCity);

  setTrendingLoading(true);

  try {
    const data = await fetchTrending(targetCity);

    console.log("fetchTrending returned:", data);

    setTrendingProducts(data.products || []);
  } catch (e) {
    console.error("TRENDING ERROR:", e);

    setTrendingProducts([]);
  } finally {
    setTrendingLoading(false);
  }
}, []);

  const setCity = useCallback((newCity) => {
  console.log("CITY CLICKED:", newCity);

  setCityRaw(newCity);

  console.log("CALLING loadTrending:", newCity);

  loadTrending(newCity);
}, [loadTrending]);

  // Load cities list + initial trending on mount
  useEffect(() => {
    fetchCities()
      .then((data) => setCities(data.cities || []))
      .catch(() => setCities(["Bangalore"]));
    loadTrending(city);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    fetch(`/api/foryou?customer_id=${customerId}&city=${encodeURIComponent(city)}`)
      .then((res) => (res.ok ? res.json() : null))
      .then((json) => {
        if (!json) return;
        setCustomerProfile({
          segment: json.customer?.segment || "working",
          tags: json.tags || [],
        });
      })
      .catch(() => {});
  }, [customerId, city]);

  const value = useMemo(
    () => ({
      // Cart
      cart,
      addProduct,
      removeItem,
      setQty,
      swapItem,
      subtotal,
      clearCart,
      hasCart: cart.length > 0,
      // Conversation
      messages,
      send,
      sendMoment,
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
      readiness,
      paymentOffers,
      gapAmount,
      // Shared response handler (reused by moments + predictions)
      applyCartResponse,
      // Data
      orderHistory: ORDER_HISTORY,
      // City & Trending
      city,
      cities,
      setCity,
      trendingProducts,
      trendingLoading,
      customerId,
      setCustomerId,
      customerProfile,
      setCustomerProfile,
    }),
    [
      cart, addProduct, removeItem, setQty,swapItem, subtotal, clearCart,
      messages, send, sendMoment, loading, error,
      themeState, cartOpen, chatOpen, meta, readiness, paymentOffers, gapAmount,
      applyCartResponse,
      city, cities, setCity, trendingProducts, trendingLoading,
      customerId, customerProfile,
    ]
  );

  return <AppCtx.Provider value={value}>{children}</AppCtx.Provider>;
}

export function useApp() {
  const ctx = useContext(AppCtx);
  if (!ctx) throw new Error("useApp must be used within AppProvider");
  return ctx;
}
