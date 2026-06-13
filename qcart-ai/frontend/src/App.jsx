import { useConversation } from "./state/useConversation.js";
import { themeFor } from "./lib/theme.js";
import ChatThread from "./components/ChatThread.jsx";
import Composer from "./components/Composer.jsx";
import MissionTiles from "./components/MissionTiles.jsx";
import CartPanel from "./components/CartPanel.jsx";
import GapNudge from "./components/GapNudge.jsx";
import SavedCounter from "./components/SavedCounter.jsx";

export default function App() {
  const c = useConversation();
  const theme = themeFor(c.meta.urgency);

  return (
    <div className="mx-auto min-h-screen max-w-5xl px-5 py-8 sm:py-12">
      {/* Header */}
      <header className="mb-7">
        <div className={`mb-3 inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-medium ${theme.chip}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${theme.dot}`} /> {theme.label}
        </div>
        <h1 className="font-display text-3xl font-bold leading-[1.05] tracking-tight sm:text-4xl">
          Don't shop. <span className="text-smart">Just say your moment.</span>
        </h1>
      </header>

      <div className="grid gap-8 md:grid-cols-[1fr_minmax(320px,400px)]">
        {/* Left — conversation */}
        <div className="flex flex-col gap-4">
          {!c.hasCart && c.messages.length === 0 && (
            <MissionTiles onPick={c.send} disabled={c.loading} />
          )}
          <ChatThread messages={c.messages} loading={c.loading} />
          {c.error && (
            <div className="rounded-2xl bg-white px-4 py-3 text-sm text-red-600 ring-1 ring-red-200">
              {c.error}
            </div>
          )}
          <Composer
            onSend={c.send}
            loading={c.loading}
            theme={theme}
            placeholder={c.hasCart ? "Refine it — “make it cheaper”, “add for kids”…" : "What's the moment? e.g. movie night for 4…"}
          />
        </div>

        {/* Right — live cart */}
        <div className="flex flex-col gap-3">
          {c.hasCart ? (
            <>
              <SavedCounter cart={c.cart} />
              <GapNudge gapAmount={c.gapAmount} fillers={c.meta.gapFillers} onAdd={c.addProduct} />
              <CartPanel
                cart={c.cart}
                subtotal={c.subtotal}
                suggestions={c.meta.suggestions}
                theme={theme}
                onQty={c.setQty}
                onRemove={c.removeItem}
                onAdd={c.addProduct}
              />
            </>
          ) : (
            <div className="grid h-40 place-items-center rounded-3xl bg-white/60 text-center text-sm text-ink/40 ring-1 ring-black/5">
              Your cart will appear here
            </div>
          )}
        </div>
      </div>

      <footer className="mt-14 text-center text-xs text-ink/30">
        QCart AI · moment-aware quick commerce · powered by Claude
      </footer>
    </div>
  );
}
