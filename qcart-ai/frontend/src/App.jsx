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
  const { cartOpen, chatOpen } = useApp();

  return (
    <div className="min-h-screen relative bg-gradient-to-b from-slate-50 via-white to-slate-50 dark:from-gray-950 dark:via-gray-900 dark:to-gray-950 text-gray-900 dark:text-gray-100 overflow-x-hidden">
      {/* Rain effect overlay for rainy theme */}
      <RainEffect />

      {/* Sticky header */}
      <Header />

      {/* Main content */}
      <main className="relative z-10">
        {/* Hero search — the star of the show */}
        <HeroSearch />

        {/* Mission Cards — quick moment selection */}
        <motion.section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12"
        >
          <MissionCards />
        </motion.section>

        {/* Buy Again — order history */}
        <motion.section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12"
        >
          <BuyAgainNow />
        </motion.section>

        {/* Offers carousel */}
        <motion.section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12"
        >
          <OfferBanners />
        </motion.section>

        {/* AI Recommendations */}
        <motion.section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12"
        >
          <AIRecommendations />
        </motion.section>

        {/* Trending Moments */}
        <motion.section
          variants={sectionVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true, margin: "-50px" }}
          className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 md:py-12"
        >
          <TrendingMoments />
        </motion.section>
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
