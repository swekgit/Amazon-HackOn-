# Requirements Document

## Introduction

QCart AI Hardening is a set of backend improvements to make the QCart AI quick-commerce assistant demo-ready for the Amazon HackOn competition. The hardening covers three areas: reliable LLM prompt behavior across six demo scenarios and three refinement commands, expanded product catalog with premium variants for tier-switching, and a tuned gap engine that produces meaningful free-delivery nudges with context-relevant fillers.

## Glossary

- **Brain**: The module (`brain.py`) responsible for constructing the LLM prompt, calling the NVIDIA NIM API, and parsing the JSON response containing cart, context, urgency, reply, and suggestions.
- **Catalog**: The product database (`data/products.json`) loaded by `catalog.py`, containing product entries with id, name, category, price, and tags.
- **Gap_Engine**: The module (`gap.py`) that computes the difference between the cart subtotal and the free-delivery threshold, and selects context-relevant filler products to close that gap.
- **Context**: A classification label assigned to a user message representing the shopping moment. Valid values: movie_night, party, health, baby, routine, late_night, other.
- **Urgency**: A classification label indicating delivery priority. Valid values: "high" (for health/baby/emergency) or "normal" (for everything else).
- **Refinement_Command**: A follow-up user message that modifies an existing cart rather than building a new one. Supported commands: "make it cheaper", "make it premium", "remove dairy", "for N people".
- **Filler**: A product suggested by the Gap_Engine to close the gap between the cart subtotal and the free-delivery threshold.
- **Tag**: A string label on a product entry used for filtering and relevance scoring (e.g., "premium", "cheap", "dairy", "movie", "fever").
- **FREE_DELIVERY_THRESHOLD**: The configurable rupee amount in the Gap_Engine above which delivery becomes free.
- **CONTEXT_TAGS**: A dictionary in the Gap_Engine mapping each Context value to a list of relevant catalog tags used for scoring filler candidates.

## Requirements

### Requirement 1: Scenario Context Classification

**User Story:** As a demo presenter, I want the Brain to classify user messages into the correct context so that the cart, suggestions, and UI adapt to the shopping moment.

#### Acceptance Criteria

1. WHEN a user message contains "movie night" (case-insensitive), THE Brain SHALL classify context as "movie_night"
2. WHEN a user message contains "party" (case-insensitive), THE Brain SHALL classify context as "party"
3. WHEN a user message contains "groceries" or "restock" (case-insensitive), THE Brain SHALL classify context as "routine"
4. WHEN a user message contains "fever" or "sick" or "cold" (case-insensitive), THE Brain SHALL classify context as "health"
5. WHEN a user message contains "baby" or "newborn" or "infant" (case-insensitive), THE Brain SHALL classify context as "baby"
6. WHEN a user message contains "late night" or "midnight" (case-insensitive), THE Brain SHALL classify context as "late_night"
7. IF a user message does not match any of the above keywords, THEN THE Brain SHALL classify context as "other"

### Requirement 2: Scenario Urgency Classification

**User Story:** As a demo presenter, I want the Brain to assign correct urgency so that the UI can highlight time-sensitive carts.

#### Acceptance Criteria

1. WHILE context is "health", THE Brain SHALL set urgency to "high"
2. WHILE context is "baby", THE Brain SHALL set urgency to "high"
3. WHILE context is "movie_night" or "party" or "routine" or "late_night" or "other", THE Brain SHALL set urgency to "normal"
4. THE Brain SHALL only output urgency values of "high" or "normal"

### Requirement 3: Scenario Cart Construction

**User Story:** As a demo presenter, I want the Brain to produce a sensible cart for each of the six demo scenarios so that the product picks match the stated moment.

#### Acceptance Criteria

1. WHEN context is "movie_night", THE Brain SHALL include products tagged "movie" or "snack" in the cart
2. WHEN context is "party", THE Brain SHALL include products tagged "party" in the cart
3. WHEN context is "health", THE Brain SHALL include products tagged "fever" or "medicine" in the cart
4. WHEN context is "baby", THE Brain SHALL include products tagged "baby" or "newparent" in the cart
5. WHEN context is "routine", THE Brain SHALL include products tagged "weekly" or "staple" in the cart
6. WHEN context is "late_night", THE Brain SHALL include products tagged "snack" or "instant" in the cart
7. THE Brain SHALL only include product IDs that exist in the Catalog
8. THE Brain SHALL include between 3 and 10 products (inclusive) in every generated cart
9. WHEN the user message specifies a number of people N, THE Brain SHALL set each item quantity to at least 1 per person (i.e., quantity equals N divided by 2, rounded up, with a minimum of 1 and a maximum of 10 per line item)
10. IF the user message does not mention a number of people, THEN THE Brain SHALL set each item quantity to 1

### Requirement 4: Cheaper Refinement Command

**User Story:** As a demo presenter, I want the "make it cheaper" command to swap items to lower-priced alternatives so that the total drops visibly.

#### Acceptance Criteria

1. WHEN the user message is "make it cheaper", THE Brain SHALL replace current cart items with products tagged "cheap" in the same category where a cheaper-tagged alternative exists, and SHALL retain items unchanged where no cheaper-tagged alternative is available
2. WHEN the user message is "make it cheaper", THE Brain SHALL produce a cart with a lower subtotal than the previous cart
3. WHEN the user message is "make it cheaper", THE Brain SHALL retain the same context classification as the previous turn
4. WHEN the user message is "make it cheaper", THE Brain SHALL preserve the quantity of each cart item from the previous turn
5. IF the user message is "make it cheaper" and no item in the current cart has a cheaper-tagged alternative available, THEN THE Brain SHALL return the cart unchanged and include a reply indicating no cheaper alternatives were found

### Requirement 5: Premium Refinement Command

**User Story:** As a demo presenter, I want the "make it premium" command to upgrade items to premium variants so that both price and item names visibly change.

#### Acceptance Criteria

1. WHEN the user message is "make it premium" (case-insensitive), THE Brain SHALL replace current cart items with products tagged "premium" where a premium-tagged product exists in the same category
2. IF a cart item has no premium-tagged counterpart in the same category, THEN THE Brain SHALL retain that item unchanged in the cart
3. WHEN the user message is "make it premium", THE Brain SHALL produce a cart with a higher subtotal than the previous cart
4. WHEN the user message is "make it premium", THE Brain SHALL retain the same context classification as the previous turn
5. IF the cart is empty when the user sends "make it premium", THEN THE Brain SHALL return a reply indicating that there is no cart to upgrade

### Requirement 6: Remove Dairy Refinement Command

**User Story:** As a demo presenter, I want "remove dairy" to drop all dairy products from the cart precisely.

#### Acceptance Criteria

1. WHEN the user message is "remove dairy", THE Brain SHALL remove all products tagged "dairy" from the cart, resulting in zero dairy-tagged products in the response cart
2. WHEN the user message is "remove dairy", THE Brain SHALL retain all products not tagged "dairy" in the cart with their original quantities and product IDs unchanged
3. WHEN the user message is "remove dairy", THE Brain SHALL retain the same context classification and urgency value as the previous turn
4. IF the user message is "remove dairy" and no products tagged "dairy" exist in the current cart, THEN THE Brain SHALL return the cart unchanged with a reply indicating no dairy items were found
5. IF the user message is "remove dairy" and all products in the current cart are tagged "dairy", THEN THE Brain SHALL return an empty cart array

### Requirement 7: Scale for People Refinement Command

**User Story:** As a demo presenter, I want "for N people" to proportionally scale quantities so the cart adapts to group size.

#### Acceptance Criteria

1. WHEN the user message contains "for N people" where N is an integer between 1 and 20 inclusive, THE Brain SHALL multiply each cart item quantity by N divided by the previous people count (defaulting to 1 if no prior people count was set), rounding up to the nearest whole number with a minimum quantity of 1 per item
2. WHEN the user message is "for N people", THE Brain SHALL retain the same product IDs in the cart without adding or removing any items
3. WHEN the user message is "for N people", THE Brain SHALL retain the same context classification as the previous turn
4. IF the user message contains "for N people" where N is less than 1 or greater than 20 or is not an integer, THEN THE Brain SHALL keep the cart unchanged and return a reply indicating the supported people range
5. IF the cart is empty when the user message contains "for N people", THEN THE Brain SHALL keep the cart empty and return a reply indicating that items must be added before scaling

### Requirement 8: Premium Catalog Variants

**User Story:** As a demo presenter, I want the Catalog to contain premium variants of common items so that the "make it premium" command has visible upgrades to switch to.

#### Acceptance Criteria

1. THE Catalog SHALL contain at least 5 products tagged "premium"
2. THE Catalog SHALL contain at least 1 premium-tagged product in each of at least 3 different categories, including beverages and snacks
3. WHEN a premium product shares the same category as a non-premium product with at least one overlapping tag, THE premium product SHALL have a price at least 50% higher than the non-premium counterpart
4. THE Catalog SHALL contain at least 3 products tagged "cheap" spanning at least 2 different categories
5. WHEN a cheap-tagged product shares the same category as a non-cheap product, THE cheap-tagged product SHALL have a lower price than at least one non-cheap product in that category
6. THE Catalog SHALL ensure that each premium-tagged product has at least one tag in common with a non-premium product in the same category to enable the Brain to match upgrades

### Requirement 9: Free Delivery Threshold Configuration

**User Story:** As a demo presenter, I want the free-delivery threshold set at a value that makes most demo carts show a gap nudge on the first turn so the feature is always visible.

#### Acceptance Criteria

1. THE Gap_Engine SHALL set FREE_DELIVERY_THRESHOLD to a value between 299 and 499 inclusive
2. WHEN a single-scenario cart (movie_night, party, health, baby, routine) is built with default quantities, THE Gap_Engine SHALL compute a non-zero gap for at least 3 of the 5 scenarios
3. THE FREE_DELIVERY_THRESHOLD SHALL be high enough that a typical 2-3 item cart falls below the threshold

### Requirement 10: Context-Relevant Filler Suggestions

**User Story:** As a demo presenter, I want filler suggestions to match the cart context so they feel natural rather than random.

#### Acceptance Criteria

1. THE Gap_Engine SHALL define CONTEXT_TAGS entries for all six contexts: movie_night, party, health, baby, routine, late_night, with each entry containing at least 2 tags
2. WHEN computing fillers, THE Gap_Engine SHALL rank candidates in descending order by the number of their product tags that overlap with the CONTEXT_TAGS for the current context, and return at most 3 filler suggestions
3. WHEN computing fillers, THE Gap_Engine SHALL exclude any product whose ID already exists in the current cart
4. IF the provided context does not match any key in CONTEXT_TAGS, THEN THE Gap_Engine SHALL fall back to a default tag set and still return fillers using that default set

### Requirement 11: Filler Gap Closure

**User Story:** As a demo presenter, I want filler suggestions to close the delivery gap so the nudge feels actionable.

#### Acceptance Criteria

1. WHEN a gap exists, THE Gap_Engine SHALL suggest between 1 and 3 filler products
2. WHEN a gap exists, THE Gap_Engine SHALL suggest fillers whose combined price brings the cart subtotal plus fillers to no more than 60 rupees above the FREE_DELIVERY_THRESHOLD and no more than the gap amount below the FREE_DELIVERY_THRESHOLD
3. THE Gap_Engine SHALL rank filler candidates by descending relevance score first, then by ascending absolute difference between the candidate price and the remaining gap amount
4. IF a gap exists and no candidate filler products qualify, THEN THE Gap_Engine SHALL return an empty fillers list

### Requirement 12: Brain JSON Output Validity

**User Story:** As a developer, I want the Brain to always return valid parseable JSON so the backend never crashes on malformed responses.

#### Acceptance Criteria

1. THE Brain SHALL return a response as a valid JSON object containing exactly the keys: reply (string), context (string matching a valid Context value), urgency (string: "high" or "normal"), cart (array of objects each with product_id, quantity, and reason), suggestions (array of objects each with product_id and reason)
2. WHEN the Brain response contains product IDs not in the Catalog in either the cart or the suggestions array, THE backend SHALL silently drop those entries from the respective array rather than crashing
3. IF the Brain returns unparseable output, THEN THE backend SHALL return HTTP 502 with an error message indicating the response was malformed
4. IF the Brain is unreachable or the request to the Brain fails for any reason other than a JSON parse error, THEN THE backend SHALL return HTTP 502 with an error message indicating the Brain could not be reached
5. IF all product IDs in the Brain cart response are invalid after validation, THEN THE backend SHALL return HTTP 404 with an error message indicating no products could be matched
6. IF the Brain response is missing any of the required keys, THEN THE backend SHALL use fallback values: reply defaults to a generic acknowledgement string, context defaults to "routine", urgency defaults to "normal", cart defaults to an empty array, suggestions defaults to an empty array
