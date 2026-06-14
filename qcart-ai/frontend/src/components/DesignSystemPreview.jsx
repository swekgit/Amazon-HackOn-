/**
 * DesignSystemPreview — Temporary verification page for design tokens.
 * Set SHOW_DESIGN_SYSTEM = true in App.jsx to view.
 * Remove before production.
 */
export default function DesignSystemPreview() {
  return (
    <div className="min-h-screen bg-canvas p-8 font-body">
      <h1 className="font-display text-3xl font-bold text-ink mb-8">
        QCart AI — Design System Preview
      </h1>

      {/* ─── Colors ──────────────────────────────────────────────── */}
      <Section title="Colors">
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
          <ColorCard name="brand" hex="#FF7A1A" className="bg-brand" />
          <ColorCard name="brand-deep" hex="#E85D04" className="bg-brand-deep" />
          <ColorCard name="brand-soft" hex="#FFE7D3" className="bg-brand-soft" dark />
          <ColorCard name="cta" hex="#FFB703" className="bg-cta" />
          <ColorCard name="cta-deep" hex="#F59E0B" className="bg-cta-deep" />
          <ColorCard name="green" hex="#0E9F6E" className="bg-green" />
          <ColorCard name="green-soft" hex="#E3F7EE" className="bg-green-soft" dark />
          <ColorCard name="blue" hex="#2D7FF9" className="bg-blue" />
          <ColorCard name="blue-soft" hex="#E7F0FE" className="bg-blue-soft" dark />
          <ColorCard name="rose" hex="#E5484D" className="bg-rose" />
          <ColorCard name="rose-soft" hex="#FDE8E8" className="bg-rose-soft" dark />
          <ColorCard name="ink" hex="#17161B" className="bg-ink" />
          <ColorCard name="muted" hex="#6E6B76" className="bg-muted" />
          <ColorCard name="line" hex="#ECEAE6" className="bg-line" dark />
          <ColorCard name="canvas" hex="#FAFAF7" className="bg-canvas ring-1 ring-black/10" dark />
          <ColorCard name="card" hex="#FFFFFF" className="bg-card ring-1 ring-black/10" dark />
        </div>
      </Section>

      {/* ─── Typography ──────────────────────────────────────────── */}
      <Section title="Typography">
        <div className="space-y-4 bg-card rounded-panel p-6 ring-1 ring-line">
          <p className="text-xs text-muted mb-4">Space Grotesk (display)</p>
          <h1 className="font-display text-4xl font-bold text-ink">H1 — Quick Commerce AI</h1>
          <h2 className="font-display text-2xl font-semibold text-ink">H2 — Cart Assistant</h2>
          <h3 className="font-display text-lg font-semibold text-ink">H3 — Section Heading</h3>

          <hr className="border-line my-6" />

          <p className="text-xs text-muted mb-4">Inter (body)</p>
          <p className="font-body text-lg text-ink">Body Large — Your cart is 75% ready for movie night.</p>
          <p className="font-body text-base text-ink">Body Medium — Add Cola to complete your party setup.</p>
          <p className="font-body text-sm text-muted">Caption — Last updated 2 minutes ago</p>
        </div>
      </Section>

      {/* ─── Border Radius ───────────────────────────────────────── */}
      <Section title="Border Radius">
        <div className="flex flex-wrap gap-4">
          <div className="w-32 h-20 bg-brand-soft ring-1 ring-brand/20 rounded-card flex items-center justify-center text-sm font-medium text-ink">
            rounded-card
          </div>
          <div className="w-32 h-20 bg-blue-soft ring-1 ring-blue/20 rounded-panel flex items-center justify-center text-sm font-medium text-ink">
            rounded-panel
          </div>
          <div className="px-6 h-10 bg-green-soft ring-1 ring-green/20 rounded-pill flex items-center justify-center text-sm font-medium text-ink">
            rounded-pill
          </div>
        </div>
      </Section>

      {/* ─── Backwards Compatibility ─────────────────────────────── */}
      <Section title="Backwards Compatibility (smart / fresh)">
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <div className="p-4 rounded-xl bg-smart text-white text-center text-sm font-medium">
            bg-smart
          </div>
          <div className="p-4 rounded-xl bg-smart-soft text-smart-dark text-center text-sm font-medium">
            bg-smart-soft + text-smart-dark
          </div>
          <div className="p-4 rounded-xl bg-white ring-1 ring-black/10 text-smart text-center text-sm font-medium">
            text-smart
          </div>
          <div className="p-4 rounded-xl bg-fresh text-white text-center text-sm font-medium">
            bg-fresh
          </div>
          <div className="p-4 rounded-xl bg-fresh-soft text-fresh text-center text-sm font-medium">
            bg-fresh-soft + text-fresh
          </div>
          <div className="p-4 rounded-xl bg-white ring-1 ring-black/10 text-fresh text-center text-sm font-medium">
            text-fresh
          </div>
        </div>
      </Section>

      {/* ─── Buttons Preview ─────────────────────────────────────── */}
      <Section title="Button Styles">
        <div className="flex flex-wrap gap-3">
          <button className="px-5 py-2.5 rounded-pill bg-brand text-white font-display font-semibold text-sm">
            Primary CTA
          </button>
          <button className="px-5 py-2.5 rounded-pill bg-cta text-ink font-display font-semibold text-sm">
            Secondary CTA
          </button>
          <button className="px-5 py-2.5 rounded-pill bg-ink text-white font-display font-semibold text-sm">
            Dark
          </button>
          <button className="px-5 py-2.5 rounded-pill ring-1 ring-line text-ink font-display font-semibold text-sm">
            Outlined
          </button>
        </div>
      </Section>
    </div>
  );
}

function Section({ title, children }) {
  return (
    <section className="mb-10">
      <h2 className="font-display text-xl font-semibold text-ink mb-4 pb-2 border-b border-line">
        {title}
      </h2>
      {children}
    </section>
  );
}

function ColorCard({ name, hex, className, dark = false }) {
  return (
    <div className={`rounded-card p-4 ${className} flex flex-col justify-end min-h-[80px]`}>
      <span className={`text-xs font-semibold ${dark ? "text-ink" : "text-white"}`}>{name}</span>
      <span className={`text-[10px] ${dark ? "text-muted" : "text-white/70"}`}>{hex}</span>
    </div>
  );
}
