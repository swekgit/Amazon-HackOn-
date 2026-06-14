import React from "react";
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
import DesignSystemPreview from "./components/DesignSystemPreview.jsx";

// Toggle to true to view design system preview — set false for production
const SHOW_DESIGN_SYSTEM = false;
const sectionVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] },
  },
};

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.12,
      delayChildren: 0.1,
    },
  },
};

export default function App() {
  const [activeTab, setActiveTab] = useState("foryou");
  const { cartOpen, chatOpen } = useApp();

  if (SHOW_DESIGN_SYSTEM) return <DesignSystemPreview />;

  return (
    <div className="min-h-screen relative bg-white text-gray-900 overflow-x-hidden">
      {/* Rain effect overlay for rainy theme */}
      <RainEffect />

      {/* Sticky header */}
      <Header />

      {/* Main content */}
      <main className="relative z-10">
        {/* Hero search — the star of the show */}
        <HeroSearch />

        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6">
  <div className="flex rounded-2xl bg-white p-1 ring-1 ring-black/5 shadow-sm">
    <button
      onClick={() => setActiveTab("foryou")}
      className={`flex-1 rounded-xl px-4 py-3 text-sm font-medium transition ${
        activeTab === "foryou"
          ? "bg-smart text-white"
          : "text-gray-600"
      }`}
    >
      For You
    </button>

    <button
      onClick={() => setActiveTab("home")}
      className={`flex-1 rounded-xl px-4 py-3 text-sm font-medium transition ${
        activeTab === "home"
          ? "bg-smart text-white"
          : "text-gray-600"
      }`}
    >
      Cart Assistant
    </button>
  </div>
</div>
{activeTab === "foryou" ? (
  <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <ForYou />
  </div>
) : (
  <>

        {/* Mission Cards — quick moment selection */}
        <motion.section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 md:py-6"
        >
          <MissionCards />

        </motion.section>

        {/* Buy Again — order history */}
        <motion.section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 md:py-6"
        >
          <BuyAgainNow />
        </motion.section>

        {/* Offers carousel */}
        <motion.section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 md:py-6"
        >
          <OfferBanners />
        </motion.section>

        {/* AI Recommendations */}
        <motion.section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 md:py-6"
        >
          <AIRecommendations />
        </motion.section>

        {/* Trending Moments */}
        <motion.section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 md:py-6"
        >
          <TrendingMoments />
        </motion.section>
          </>
)}
      </main>

      {/* Footer */}
      <Footer />

      {/* Cart drawer overlay */}
      <AnimatePresence>{cartOpen && <CartDrawer />}</AnimatePresence>

      {/* Conversational AI panel overlay */}
      <AnimatePresence>{chatOpen && <ConversationalPanel />}</AnimatePresence>

      {/* Floating copilot button */}
      <CopilotFAB />
    </div>
  );
}
