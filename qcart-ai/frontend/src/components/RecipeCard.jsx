import { motion } from "framer-motion";
import { ChefHat, Users, CheckCircle2 } from "lucide-react";

/**
 * Task 7 — Recipe Card.
 * Rendered when recipe.is_recipe === true.
 * Shows: dish name, servings, "Already have" from recipe.skipped [{name, why}].
 * Missing ingredients are shown by the normal CartItem list — no duplication here.
 */
export default function RecipeCard({ recipe }) {
  if (!recipe?.is_recipe) return null;

  const skipped = recipe.skipped || []; // [{name, why}, ...]

  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      className="rounded-xl bg-amber-50 p-4 ring-1 ring-amber-200"
    >
      {/* Header */}
      <div className="flex items-center gap-2 mb-3">
        <div className="grid h-8 w-8 place-items-center rounded-full bg-amber-100">
          <ChefHat size={16} className="text-amber-700" />
        </div>
        <div>
          <p className="text-sm font-bold text-amber-900">{recipe.dish || "Recipe"}</p>
          {recipe.servings && (
            <p className="flex items-center gap-1 text-[11px] text-amber-700">
              <Users size={10} /> {recipe.servings} servings
            </p>
          )}
        </div>
      </div>

      {/* Already have — from recipe.skipped only */}
      {skipped.length > 0 && (
        <div>
          <p className="text-[10px] font-semibold text-amber-700/60 uppercase tracking-wider mb-1">
            Already have
          </p>
          <div className="flex flex-wrap gap-1">
            {skipped.map((item, i) => (
              <span
                key={item.name ?? i}
                title={item.why}
                className="inline-flex items-center gap-1 rounded-full bg-green-soft px-2 py-0.5 text-[10px] font-medium text-green ring-1 ring-green/15"
              >
                <CheckCircle2 size={9} />
                {item.name}
              </span>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  );
}
