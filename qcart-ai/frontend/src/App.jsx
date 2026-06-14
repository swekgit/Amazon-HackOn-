import { motion, AnimatePresence } from "framer-motion";
import Header from "./components/Header.jsx";
import HeroSearch from "./components/HeroSearch.jsx";
import MissionCards from "./components/MissionCards.jsx";
import BuyAgainNow from "./components/BuyAgainNow.jsx";
import OfferBanners from "./components/OfferBanners.jsx";
import AIRecommendations from "./components/AIRecommendations.jsx";
import TrendingMoments from "./components/TrendingMoments.jsx";
import Footer from "./components/Footer.jsx";
import CartDrawer from "./components/CartDrawer.jsx";
import ConversationalPanel from "./components/ConversationalPanel.jsx";
import CopilotFAB from "./components/CopilotFAB.jsx";
import RainEffect from "./components/RainEffect.jsx";
import { useApp } from "./state/AppContext.jsx";
import { useState } from "react";
import ForYou from "./components/ForYou";

const sectionVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] },
  },
};

export default function App() {
  const [activeTab, setActiveTab] = useState("foryou");
  const { cartOpen, chatOpen } = useApp();

  return (
    <div className="min-h-screen relative bg-canvas text-ink overflow-x-hidden">
      <RainEffect />
      <Header />

      <main className="relative z-10">
        {/* Hero search — always visible */}
        <HeroSearch />

        {/* Tabs */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-4">
          <div className="flex rounded-2xl bg-white p-1 ring-1 ring-line shadow-sm">
            <button
              onClick={() => setActiveTab("foryou")}
              className={`flex-1 rounded-xl px-4 py-2.5 text-sm font-semibold transition ${
                activeTab === "foryou"
                  ? "bg-brand text-white shadow-sm"
                  : "text-muted hover:text-ink"
              }`}
            >
              For You
            </button>
            <button
              onClick={() => setActiveTab("assistant")}
              className={`flex-1 rounded-xl px-4 py-2.5 text-sm font-semibold transition ${
                activeTab === "assistant"
                  ? "bg-brand text-white shadow-sm"
                  : "text-muted hover:text-ink"
              }`}
            >
              Cart Assistant
            </button>
          </div>
        </div>

        {/* Tab content — explicit matching */}
        {activeTab === "foryou" && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
            <ForYou />
          </div>
        )}

        {activeTab === "assistant" && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 space-y-4 md:space-y-6">
            <motion.section variants={sectionVariants} initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }}>
              <MissionCards />
            </motion.section>

            <motion.section variants={sectionVariants} initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }}>
              <BuyAgainNow />
            </motion.section>

            <motion.section variants={sectionVariants} initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }}>
              <OfferBanners />
            </motion.section>

            <motion.section variants={sectionVariants} initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }}>
              <AIRecommendations />
            </motion.section>

            <motion.section variants={sectionVariants} initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }}>
              <TrendingMoments />
            </motion.section>
          </div>
        )}
      </main>

      <Footer />

      {/* Overlays */}
      <AnimatePresence>{cartOpen && <CartDrawer />}</AnimatePresence>
      <AnimatePresence>{chatOpen && <ConversationalPanel />}</AnimatePresence>
      <CopilotFAB />
    </div>
  );
}
