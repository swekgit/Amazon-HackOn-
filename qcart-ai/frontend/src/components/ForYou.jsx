import { useEffect, useState } from "react";
import { Loader2, Sparkles, Tag } from "lucide-react";
import { useApp } from "../state/AppContext.jsx";
import ProductCard from "./ProductCard.jsx";
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

const S3 = "https://qcart-ai-apoorva-images.s3.ap-south-1.amazonaws.com/products/";

/** Normalise any product shape so ProductCard always gets .image */
function withImage(product) {
  if (!product) return product;
  return {
    ...product,
    image: product.image || `${product.id}.jpg`,
  };
}

export default function ForYou() {
  const { city, addProduct, customerId, setCustomerId, setCustomerProfile } = useApp();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
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
      if (!res.ok) throw new Error("Failed to load recommendations");
      const json = await res.json();
      setData(json);
      setCustomerProfile({
        segment: json.customer?.segment || "working",
        tags: json.tags || [],
      });
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
      {/* 1. Header */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="font-display text-2xl text-ink">For You</h1>
          <p className="text-sm text-ink/60">Personalised picks based on your preferences</p>
        </div>
        {/* 2. Customer selector */}
        <select
          value={customerId}
          onChange={(e) => setCustomerId(e.target.value)}
          className="rounded-xl border border-black/10 bg-white px-4 py-2 text-sm shadow-sm outline-none focus:ring-2 focus:ring-smart"
        >
          {CUSTOMERS.map((c) => (
            <option key={c.value} value={c.value}>{c.label}</option>
          ))}
        </select>
      </div>

      {/* Loading */}
      {loading && (
        <div className="flex items-center justify-center gap-3 py-16">
          <Loader2 className="h-5 w-5 animate-spin" />
          <span>Loading recommendations...</span>
        </div>
      )}

      {/* Error */}
      {!loading && error && (
        <div className="rounded-2xl border border-red-200 bg-red-50 p-4 text-red-600">{error}</div>
      )}

      {!loading && !error && data && (
        <>
          {/* 3. Customer profile / tags */}
          {data.tags?.length > 0 && (
            <section className="space-y-2">
              <h2 className="font-display text-sm font-semibold text-ink/50 uppercase tracking-wider">Your Profile</h2>
              <div className="flex flex-wrap gap-2">
                {data.tags.map((tag) => (
                  <span key={tag} className="rounded-full bg-smart-soft px-3 py-1 text-xs font-medium text-smart">
                    {tag}
                  </span>
                ))}
              </div>
            </section>
          )}

          {/* 4. Predicted For You */}
          <PredictedForYouCard
            predictions={predictions}
            onAddKit={(prediction) => prediction.cart?.forEach((item) => addProduct(item))}
          />

          {/* 5. Recommended */}
          {data.recommended?.length > 0 && (
            <section className="space-y-4">
              <div className="flex items-center gap-2">
                <Sparkles className="h-5 w-5 text-brand" />
                <h2 className="font-display text-xl">Recommended for you</h2>
              </div>
              <div className="grid gap-4 grid-cols-1 min-[360px]:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
                {data.recommended.map((product, i) => (
                  <ProductCard
                    key={product.id}
                    product={withImage(product)}
                    subtitle={product.reason}
                    index={i}
                  />
                ))}
              </div>
            </section>
          )}

          {/* 6. Deals */}
          {data.deals?.length > 0 && (
            <section className="space-y-4">
              <div className="flex items-center gap-2">
                <Tag className="h-5 w-5 text-fresh" />
                <h2 className="font-display text-xl">Deals for you</h2>
              </div>
              <div className="grid gap-4 grid-cols-1 min-[360px]:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
                {data.deals.map((deal, i) => (
                  <ProductCard
                    key={deal.id}
                    product={withImage({ ...deal, price: deal.discounted_price ?? deal.price })}
                    badge={deal.discount_pct ? `${deal.discount_pct}% OFF` : deal.offer_label}
                    badgeColor="bg-fresh"
                    oldPrice={deal.price}
                    subtitle={deal.pitch || deal.offer_label}
                    index={i}
                  />
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </div>
  );
}
