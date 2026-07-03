import { useState, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Header from "./components/Header.jsx";
import HeroSearch from "./components/HeroSearch.jsx";
import SlimAssistantBar from "./components/SlimAssistantBar.jsx";
import AIAssistantPanel from "./components/AIAssistantPanel.jsx";
import MissionCards from "./components/MissionCards.jsx";
import BuyAgainNow from "./components/BuyAgainNow.jsx";
import OfferBanners from "./components/OfferBanners.jsx";
import TrendingMoments from "./components/TrendingMoments.jsx";
import TrendingInCity from "./components/TrendingInCity.jsx";
import ForYou from "./components/ForYou";
import Footer from "./components/Footer.jsx";
import CartDrawer from "./components/CartDrawer.jsx";
import ConversationalPanel from "./components/ConversationalPanel.jsx";
import CopilotFAB from "./components/CopilotFAB.jsx";
import RainEffect from "./components/RainEffect.jsx";
import { useApp } from "./state/AppContext.jsx";
import { detectMomentFromText } from "./data/momentContexts.js";

const sectionVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] },
  },
};

const TAB_KEYS = { FOR_YOU: "forYou", CART_ASSISTANT: "cartAssistant" };

export default function App() {
  const { cartOpen, chatOpen, loading, hasCart, messages } = useApp();

  // ── Tab state (local UI only) ──────────────────────────────
  const [activeTab, setActiveTab] = useState(TAB_KEYS.FOR_YOU);

  // Tracks which moment was detected (for contextual AI panel)
  const [detectedMoment, setDetectedMoment] = useState(null);

  // AI Assistant panel appears when AI is working or has results
  const showAssistant = loading || hasCart || messages.length > 0;

  // Keyword inference from hero search text
  const handleSearchSubmit = useCallback((text) => {
    const moment = detectMomentFromText(text);
    if (moment) setDetectedMoment(moment);
  }, []);

  // Called from MissionCards when a moment is selected
  const handleMomentSelect = useCallback((momentKey) => {
    setDetectedMoment(momentKey);
  }, []);

  return (
    <div className="min-h-screen relative bg-white text-gray-900 overflow-x-hidden">
      <RainEffect />
      <Header />

      <main className="relative z-10">
        {/* Hero search — always visible */}
        <HeroSearch onSubmit={handleSearchSubmit} />

        {/* Slim inline assistant — appears below search when AI is active */}
        <SlimAssistantBar />

        {/* ── Segmented Toggle ─────────────────────────────────── */}
        <div className="segmented-toggle-wrapper">
          <div className="segmented-toggle" role="tablist" aria-label="Page view toggle">
            <button
              role="tab"
              aria-selected={activeTab === TAB_KEYS.FOR_YOU}
              className={`segmented-toggle__tab ${activeTab === TAB_KEYS.FOR_YOU ? "segmented-toggle__tab--active" : ""}`}
              onClick={() => setActiveTab(TAB_KEYS.FOR_YOU)}
            >
              For You
            </button>
            <button
              role="tab"
              aria-selected={activeTab === TAB_KEYS.CART_ASSISTANT}
              className={`segmented-toggle__tab ${activeTab === TAB_KEYS.CART_ASSISTANT ? "segmented-toggle__tab--active" : ""}`}
              onClick={() => setActiveTab(TAB_KEYS.CART_ASSISTANT)}
            >
              Cart Assistant
            </button>
          </div>
        </div>

        {/* ── Tab Content ──────────────────────────────────────── */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 space-y-6">

          {/* ═══════════════════════════════════════════════════════
               FOR YOU TAB
               - Customer Profile tags
               - Recommended For You
               - Deals For You
               - Trending In Your City
             ═══════════════════════════════════════════════════════ */}
          <AnimatePresence mode="wait">
            {activeTab === TAB_KEYS.FOR_YOU && (
              <motion.div
                key="forYou"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                className="space-y-6"
              >
                {/* ForYou — Customer Profile + Recommended + Deals + Trending */}
                <motion.section variants={sectionVariants} initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }}>
                  <ForYou />
                </motion.section>

                {/* Trending in City */}
                <motion.section variants={sectionVariants} initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }}>
                  <TrendingInCity />
                </motion.section>
              </motion.div>
            )}
          </AnimatePresence>

          {/* ═══════════════════════════════════════════════════════
               CART ASSISTANT TAB
               1. Cart Assistant Panel (AI summary, readiness, etc.)
               2. What's Your Moment (MissionCards)
               3. Buy Again
               4. Deals & Offers
               5. Trending Now
             ═══════════════════════════════════════════════════════ */}
          <AnimatePresence mode="wait">
            {activeTab === TAB_KEYS.CART_ASSISTANT && (
              <motion.div
                key="cartAssistant"
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.3, ease: [0.22, 1, 0.36, 1] }}
                className="space-y-6"
              >
                {/* 1. Cart Assistant Panel — AI summary, readiness, add-ons */}
                <AnimatePresence>
                  {showAssistant && (
                    <AIAssistantPanel detectedMoment={detectedMoment} />
                  )}
                </AnimatePresence>

                {/* 2. What's Your Moment — scenario cards */}
                <motion.section variants={sectionVariants} initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }}>
                  <MissionCards onMomentSelect={handleMomentSelect} />
                </motion.section>

                {/* 3. Buy Again — order history */}
                <motion.section variants={sectionVariants} initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }}>
                  <BuyAgainNow />
                </motion.section>

                {/* 4. Deals & Offers */}
                <motion.section variants={sectionVariants} initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }}>
                  <OfferBanners />
                </motion.section>

                {/* 5. Trending Now */}
                <motion.section variants={sectionVariants} initial="hidden" whileInView="visible" viewport={{ once: true, margin: "-50px" }}>
                  <TrendingMoments />
                </motion.section>
              </motion.div>
            )}
          </AnimatePresence>

        </div>
      </main>

      <Footer />

      {/* Overlays */}
      <AnimatePresence>{cartOpen && <CartDrawer />}</AnimatePresence>
      <AnimatePresence>{chatOpen && <ConversationalPanel />}</AnimatePresence>
      <CopilotFAB />
    </div>
  );
}
