# Implementation Plan: QCart AI Hardening

## Overview

Harden the QCart AI backend for reliable demo behavior across six scenarios and four refinement commands. Work is split into three tracks: expand the product catalog with premium/cheap variants, tune the gap engine for meaningful free-delivery nudges, harden the brain prompt for deterministic LLM output, and add validation/fallback logic in the API layer.

## Tasks

- [x] 1. Expand product catalog with premium and cheap variants
  - [x] 1.1 Add premium and cheap product entries to `data/products.json`
    - Add at least 1 premium-tagged product in a category other than beverages/snacks (e.g., staples or produce) to meet the ≥3 categories requirement
    - Add at least 1 more cheap-tagged product to reach ≥3 cheap products spanning ≥2 categories
    - Ensure every premium product is ≥50% more expensive than its non-premium counterpart in the same category
    - Ensure each premium product shares at least one non-tier tag with a non-premium product in the same category
    - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6_

  - [ ]* 1.2 Write property tests for catalog invariants (`tests/test_catalog_properties.py`)
    - **Property 2: Premium price invariant** — for any premium/non-premium pair in the same category sharing a non-tier tag, premium price ≥ 1.5× non-premium price
    - **Property 3: Cheap price invariant** — for any cheap-tagged product, at least one non-cheap product in the same category has a higher price
    - **Property 4: Premium tag overlap invariant** — for any premium product, at least one non-premium product in the same category shares a non-tier tag
    - **Validates: Requirements 8.3, 8.5, 8.6**

  - [ ]* 1.3 Write smoke tests for catalog constraints (`tests/test_smoke_catalog.py`)
    - Assert ≥5 premium products in catalog
    - Assert premium products span ≥3 categories
    - Assert ≥3 cheap products spanning ≥2 categories
    - Assert CONTEXT_TAGS has all 6 contexts with ≥2 tags each
    - Assert FREE_DELIVERY_THRESHOLD is between 299 and 499
    - _Requirements: 8.1, 8.2, 8.4, 9.1, 10.1_

- [x] 2. Tune the gap engine (`gap.py`)
  - [x] 2.1 Raise FREE_DELIVERY_THRESHOLD and expand CONTEXT_TAGS
    - Change `FREE_DELIVERY_THRESHOLD` from 199 to 399
    - Add "medicine" tag to the health context entry in CONTEXT_TAGS
    - Ensure all six contexts have ≥2 tags each (verify existing entries)
    - Add fallback logic: if context not in CONTEXT_TAGS, use `["snack", "staple"]`
    - _Requirements: 9.1, 9.2, 9.3, 10.1, 10.4_

  - [x] 2.2 Implement improved filler scoring and overshoot guard
    - Refine scoring: primary sort by tag-overlap count (descending), secondary by ascending absolute difference between candidate price and remaining gap
    - Add overshoot guard: combined filler prices must not exceed gap + 60
    - Ensure fillers exclude products already in the cart
    - Ensure at most 3 fillers are returned
    - Return empty fillers list when no candidates qualify
    - _Requirements: 10.2, 10.3, 11.1, 11.2, 11.3, 11.4_

  - [ ]* 2.3 Write property tests for gap engine (`tests/test_gap_properties.py`)
    - **Property 5: Filler ordering correctness** — fillers ordered by descending relevance then ascending gap-closeness
    - **Property 6: Filler exclusion from cart** — no filler ID appears in the input cart
    - **Property 7: Filler fallback on unknown context** — unknown context still produces fillers using default tags
    - **Property 8: Filler count bounds** — between 1 and 3 fillers when gap exists and candidates qualify
    - **Property 9: Filler overshoot guard** — cart subtotal + fillers total ≤ threshold + 60
    - **Validates: Requirements 10.2, 10.3, 10.4, 11.1, 11.2, 11.3**

- [x] 3. Checkpoint - Core data and gap engine
  - Ensure all tests pass, ask the user if questions arise.

- [x] 4. Harden the Brain prompt (`brain.py`)
  - [x] 4.1 Rewrite INSTRUCTIONS with explicit classification and refinement rules
    - Add explicit context-mapping keyword rules (case-insensitive): "movie night" → movie_night, "party" → party, "fever"/"sick"/"cold" → health, "baby"/"newborn"/"infant" → baby, "groceries"/"restock" → routine, "late night"/"midnight" → late_night, default → other
    - Add explicit urgency rules: health/baby → "high", everything else → "normal"
    - Add refinement command blocks: "make it cheaper" swaps to cheap-tagged, "make it premium" swaps to premium-tagged, "remove dairy" drops dairy-tagged, "for N people" scales quantities
    - Add cart size constraint: 3–10 products per generated cart
    - Add quantity rules: default quantity 1 unless people count specified (N/2 rounded up, min 1, max 10)
    - _Requirements: 1.1–1.7, 2.1–2.4, 3.1–3.10, 4.1–4.5, 5.1–5.5, 6.1–6.5, 7.1–7.5_

  - [x] 4.2 Lower temperature and add JSON guardrails
    - Lower `temperature` to 0.2 for more deterministic output
    - Add explicit "RESPOND WITH ONLY VALID JSON — no markdown, no explanation" at the end of the prompt
    - Ensure the prompt repeats the JSON schema shape as a reminder
    - _Requirements: 12.1_

- [x] 5. Add validation and fallback logic in API layer (`main.py`)
  - [x] 5.1 Implement fallback defaults for missing Brain response keys
    - If `reply` missing, default to "Here's your cart."
    - If `context` missing, default to "routine"
    - If `urgency` missing, default to "normal"
    - If `cart` missing, default to empty array
    - If `suggestions` missing, default to empty array
    - Apply fallbacks before enrichment step
    - _Requirements: 12.1, 12.6_

  - [x] 5.2 Validate Brain response structure and handle edge cases
    - Silently drop invalid product IDs from cart and suggestions arrays (existing behavior, verify)
    - Return HTTP 502 on JSONDecodeError (existing behavior, verify)
    - Return HTTP 502 on network/API errors (existing behavior, verify)
    - Return HTTP 404 when all cart product IDs are invalid after enrichment
    - Ensure urgency is validated to only "high" or "normal" (default to "normal" otherwise)
    - Ensure context is validated to allowed values (default to "routine" otherwise)
    - _Requirements: 12.2, 12.3, 12.4, 12.5_

  - [ ]* 5.3 Write property tests for validation and fallback (`tests/test_validation_properties.py`)
    - **Property 1: Invalid product IDs are dropped by enrichment** — enrichment output contains only valid catalog IDs
    - **Property 10: Fallback defaults on missing Brain keys** — any subset of missing keys produces a complete response with all keys present
    - **Validates: Requirements 3.7, 12.1, 12.2, 12.6**

  - [ ]* 5.4 Write unit tests for error handling (`tests/test_error_handling.py`)
    - Test: Brain returns non-JSON → HTTP 502
    - Test: Brain unreachable → HTTP 502
    - Test: All IDs invalid → HTTP 404
    - Test: Empty message → HTTP 400
    - Test: Missing keys in brain response → fallback defaults applied
    - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [x] 6. Checkpoint - Brain and API validation
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Integration wiring and scenario verification
  - [x] 7.1 Set up test infrastructure (`tests/__init__.py`, `conftest.py`)
    - Create `backend/tests/` directory with `__init__.py`
    - Create `conftest.py` with shared fixtures: sample carts, mock brain responses, catalog access
    - Add `hypothesis` and `pytest` to `requirements.txt`
    - _Requirements: all_

  - [ ]* 7.2 Write integration tests for demo scenarios (`tests/test_integration_scenarios.py`)
    - Test all six scenarios produce correct context classification
    - Test urgency mapping: health/baby → high, others → normal
    - Test cart products match expected tags per scenario
    - Test refinement commands modify cart correctly (premium, cheaper, remove dairy, for N people)
    - _Requirements: 1.1–1.7, 2.1–2.4, 3.1–3.6, 4.1–4.5, 5.1–5.5, 6.1–6.5, 7.1–7.5_

- [x] 8. Final checkpoint - Full integration
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional and can be skipped for faster MVP
- Each task references specific requirements for traceability
- Checkpoints ensure incremental validation
- Property tests validate universal correctness properties from the design document
- Unit tests validate specific examples and edge cases
- The design uses Python (FastAPI + Hypothesis) — all implementation is in Python
- Test infrastructure (task 7.1) can be set up earlier if preferred, but is placed here to keep implementation tasks focused first

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1", "7.1"] },
    { "id": 1, "tasks": ["1.2", "1.3", "2.1"] },
    { "id": 2, "tasks": ["2.2"] },
    { "id": 3, "tasks": ["2.3", "4.1"] },
    { "id": 4, "tasks": ["4.2", "5.1"] },
    { "id": 5, "tasks": ["5.2"] },
    { "id": 6, "tasks": ["5.3", "5.4"] },
    { "id": 7, "tasks": ["7.2"] }
  ]
}
```
