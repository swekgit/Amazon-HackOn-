import { useEffect, useState } from "react";
import { Loader2, Sparkles, Tag, TrendingUp } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import PredictedForYouCard from "./PredictedForYouCard.jsx";

const CUSTOMERS = [
  { label: "Ravi", value: "cust_ravi" },
  { label: "Priya", value: "cust_priya" },
  { label: "Aarav", value: "cust_aarav" },
  { label: "Sneha", value: "cust_sneha" },
  { label: "Karan", value: "cust_karan" },
  { label: "Ananya", value: "cust_ananya" },
  { label: "Rohan", value: "cust_rohan" },
  { label: "Meera", value: "cust_meera" },
];

export default function ForYou({ }) {
  const [customerId, setCustomerId] = useState("cust_ananya");
  const { city, addProduct, cart, setQty, removeItem } = useApp();
  const [data, setData] = useState(null);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [trending, setTrending] = useState(null);
  const [predictions, setPredictions] = useState([]);

  useEffect(() => {
    loadForYou(customerId);
    loadPredictions(customerId);
  }, [customerId, city]);

  async function loadForYou(id) {
    try {
      setLoading(true);
      setError("");

      const res = await fetch(`/api/foryou?customer_id=${id}`);

      if (!res.ok) {
        throw new Error("Failed to load recommendations");
      }

      const json = await res.json();
      setData(json);

      try {
        const trendRes = await fetch(
          `/api/trending?city=${encodeURIComponent(city)}`
        );

        if (trendRes.ok) {
          const trendJson = await trendRes.json();
          setTrending(trendJson);
        }
      } catch {
        setTrending(null);
      }
    } catch (err) {
      setError(err.message || "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  async function loadPredictions(id) {
    try {
      const res = await fetch(`/api/predicted?customer_id=${id}`);
      if (!res.ok) throw new Error("predictions failed");
      const json = await res.json();
      setPredictions(json.predictions || []);
    } catch {
      setPredictions([]);
    }
  }

  return (
    <div className="space-y-8">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-2xl text-ink">
            Personalized Shopping
          </h1>
          <p className="text-sm text-ink/60">
            Recommendations generated from customer preferences
          </p>
        </div>

        <select
          value={customerId}
          onChange={(e) => setCustomerId(e.target.value)}
          className="rounded-xl border border-black/10 bg-white px-4 py-2 text-sm shadow-sm outline-none focus:ring-2 focus:ring-smart"
        >
          {CUSTOMERS.map((customer) => (
            <option key={customer.value} value={customer.value}>
              {customer.label}
            </option>
          ))}
        </select>
      </div>

      <PredictedForYouCard
        predictions={predictions}
        onAddKit={(prediction) => {
          prediction.cart?.forEach((item) => addProduct(item));
        }}
      />

      {loading && (
        <div className="flex items-center justify-center gap-3 py-16">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Loading recommendations...</span>
        </div>
      )}

      {!loading && error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-red-600">
          {error}
        </div>
      )}

      {!loading && !error && data && (
        <>
          <section className="space-y-3">
            <h2 className="font-display text-lg text-ink">
              Customer Profile
            </h2>
            <div className="flex flex-wrap gap-2">
              {data.tags?.map((tag) => (
                <span
                  key={tag}
                  className="rounded-full bg-smart-soft px-3 py-1 text-xs font-medium text-smart"
                >
                  {tag}
                </span>
              ))}
            </div>
          </section>

          <section className="space-y-4">
            <div className="flex items-center gap-2">
              <Sparkles className="h-5 w-5" />
              <h2 className="font-display text-xl">
                Recommended for you
              </h2>
            </div>

            <div className="grid gap-4 grid-cols-1 min-[360px]:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
              {data.recommended?.map((product) => {
                const qty =
                  cart.find((i) => i.id === product.id)?.quantity || 0;

                return (
                  <div
                    key={product.id}
                    className="rounded-3xl bg-white p-5 ring-1 ring-black/5"
                  >
                    <div className="space-y-3">
                      <div>
                        <h3 className="font-display text-lg text-ink">
                          {product.name}
                        </h3>
                        <p className="font-display text-xl">
                          ₹{product.price}
                        </p>
                      </div>

                      <p className="text-sm text-ink/60">
                        {product.reason}
                      </p>

                      {qty > 0 ? (
                        <div className="flex items-center justify-between rounded-xl border border-black/10">
                          <button
                            onClick={() =>
                              qty <= 1
                                ? removeItem(product.id)
                                : setQty(product.id, qty - 1)
                            }
                            className="px-4 py-2 text-lg"
                          >
                            -
                          </button>
                          <span className="font-medium">{qty}</span>
                          <button
                            onClick={() => setQty(product.id, qty + 1)}
                            className="px-4 py-2 text-lg"
                          >
                            +
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() => addProduct(product)}
                          className="w-full rounded-xl bg-smart px-4 py-2 text-sm font-medium text-white transition hover:scale-[1.02]"
                        >
                          Add
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>

          <section className="space-y-4">
            <div className="flex items-center gap-2">
              <Tag className="h-5 w-5" />
              <h2 className="font-display text-xl">
                Deals for you
              </h2>
            </div>

            <div className="grid gap-4 grid-cols-1 min-[360px]:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
              {data.deals?.map((deal) => {
                const qty =
                  cart.find((i) => i.id === deal.id)?.quantity || 0;

                return (
                  <div
                    key={deal.id}
                    className="relative rounded-3xl bg-white p-5 ring-1 ring-black/5"
                  >
                    <div className="absolute right-4 top-4 rounded-full bg-fresh px-2.5 py-1 text-xs font-semibold text-white">
                      {deal.discount_pct}% OFF
                    </div>

                    <div className="space-y-3">
                      <div>
                        <h3 className="font-display text-lg text-ink pr-16">
                          {deal.name}
                        </h3>
                        <div className="mt-2 flex items-center gap-2">
                          <span className="font-display text-2xl">
                            ₹{deal.discounted_price}
                          </span>
                          <span className="text-sm text-ink/40 line-through">
                            ₹{deal.price}
                          </span>
                        </div>
                      </div>

                      <span className="inline-flex rounded-full bg-fresh-soft px-3 py-1 text-xs font-medium text-fresh">
                        {deal.offer_label}
                      </span>

                      <p className="text-sm text-ink/60">
                        {deal.pitch}
                      </p>

                      {qty > 0 ? (
                        <div className="flex items-center justify-between rounded-xl border border-black/10">
                          <button
                            onClick={() =>
                              qty <= 1
                                ? removeItem(deal.id)
                                : setQty(deal.id, qty - 1)
                            }
                            className="px-4 py-2 text-lg"
                          >
                            -
                          </button>
                          <span className="font-medium">{qty}</span>
                          <button
                            onClick={() => setQty(deal.id, qty + 1)}
                            className="px-4 py-2 text-lg"
                          >
                            +
                          </button>
                        </div>
                      ) : (
                        <button
                          onClick={() =>
                            addProduct({
                              ...deal,
                              price: deal.discounted_price,
                            })
                          }
                          className="w-full rounded-xl bg-fresh px-4 py-2 text-sm font-medium text-white transition hover:scale-[1.02]"
                        >
                          Add
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
