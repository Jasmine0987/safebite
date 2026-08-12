"""
Allergen Knowledge Base
========================
Covers the 9 major food allergens recognized under U.S. law (FALCPA 2004 +
the FASTER Act 2021, which added sesame as the 9th): milk, egg, fish,
crustacean shellfish, tree nuts, peanuts, wheat, soybeans, sesame.

Aliases per allergen are hand-compiled from general public knowledge of
how these ingredients commonly appear on labels (scientific/Latin names,
derivative names like "casein" for milk, E-numbers where relevant) — not
copied from any single source. For a real product, replace/expand this
with data actually sourced from:
  - FARE (Food Allergy Research & Education) — publishes practical
    ingredient-naming guidance per allergen; closest thing to an industry
    standard alias list, but it's guidance text, not a downloadable
    structured dataset — you'd transcribe it yourself.
  - EU FIC Regulation — adds mustard, celery, lupin, sulphites, and
    molluscs to the 9 above (14 total EU-regulated allergens) plus formal
    E-number mappings.
  - Open Food Facts (openfoodfacts.org, ODbL license — requires
    attribution) — has an `allergens` and `traces` field per product,
    useful for cross-checking your alias list against real label text
    at scale, not as a primary alias source itself.

This file intentionally stays plain Python data (not a DB table) since
it's a small, fixed reference vocabulary — same reasoning as the original
INGREDIENT_KB it replaces.
"""

# Canonical allergen tags used across INGREDIENT_KB, SWAP_CATALOG, and
# user profiles. Keep these as the single source of truth for spelling.
ALLERGEN_TAGS = [
    "milk", "egg", "fish", "shellfish", "tree_nut",
    "peanut", "wheat", "soy", "sesame",
]

INGREDIENT_KB = {
    # --- Milk / dairy ---
    "milk": {
        "name": "Milk / Dairy",
        "aliases": [
            "milk", "dairy", "whey", "whey protein", "casein", "caseinate",
            "lactose", "lactalbumin", "buttermilk", "ghee", "curds",
            "milk solids", "milk powder", "nonfat milk solids",
        ],
        "allergen_tags": ["milk"],
        "plainLanguage": "Derived from cow's milk — includes whey and casein even when 'milk' isn't listed directly.",
        "whyForYouTemplate": "Flagged because dairy is on your allergen profile.",
    },
    # --- Egg ---
    "egg": {
        "name": "Egg",
        "aliases": [
            "egg", "eggs", "albumin", "albumen", "ovalbumin", "egg white",
            "egg yolk", "mayonnaise", "meringue", "lysozyme",
        ],
        "allergen_tags": ["egg"],
        "plainLanguage": "Whole egg or an egg-derived protein.",
        "whyForYouTemplate": "Flagged because egg is on your allergen profile.",
    },
    # --- Fish ---
    "fish": {
        "name": "Fish",
        "aliases": [
            "fish", "anchovy", "anchovies", "cod", "salmon", "tuna",
            "tilapia", "fish sauce", "fish oil", "surimi", "worcestershire",
        ],
        "allergen_tags": ["fish"],
        "plainLanguage": "Fish or a fish-derived ingredient — includes hidden sources like Worcestershire sauce (often contains anchovy) and fish sauce.",
        "whyForYouTemplate": "Flagged because fish is on your allergen profile.",
    },
    # --- Crustacean shellfish ---
    "shellfish": {
        "name": "Shellfish",
        "aliases": [
            "shrimp", "prawn", "prawns", "crab", "lobster", "crayfish",
            "crawfish", "shellfish",
        ],
        "allergen_tags": ["shellfish"],
        "plainLanguage": "Crustacean shellfish (shrimp, crab, lobster) — one of the most severe common allergens.",
        "whyForYouTemplate": "Flagged because shellfish is on your allergen profile.",
    },
    # --- Tree nuts (FDA labeling treats coconut as a tree nut) ---
    "tree_nut": {
        "name": "Tree Nut",
        "aliases": [
            "almond", "almonds", "cashew", "cashews", "walnut", "walnuts",
            "pecan", "pecans", "pistachio", "pistachios", "hazelnut",
            "hazelnuts", "macadamia", "brazil nut", "pine nut", "coconut",
            "nut butter", "praline",
        ],
        "allergen_tags": ["tree_nut"],
        "plainLanguage": "A tree nut or tree-nut derivative. Note: FDA labeling rules classify coconut as a tree nut even though it's botanically a fruit.",
        "whyForYouTemplate": "Flagged because tree nut is on your allergen profile.",
    },
    # --- Peanut ---
    "peanut": {
        "name": "Peanut",
        "aliases": [
            "peanut", "peanuts", "groundnut", "groundnuts", "arachis oil",
            "arachis hypogaea", "peanut butter", "peanut flour",
        ],
        "allergen_tags": ["peanut"],
        "plainLanguage": "A legume, botanically unrelated to tree nuts, but one of the most common and severe food allergens.",
        "whyForYouTemplate": "Flagged because peanut is on your allergen profile.",
    },
    # --- Wheat / gluten ---
    "wheat": {
        "name": "Wheat",
        "aliases": [
            "wheat", "wheat flour", "enriched wheat flour", "durum",
            "semolina", "spelt", "farina", "graham flour", "bulgur",
            "seitan", "vital wheat gluten",
        ],
        "allergen_tags": ["wheat"],
        "plainLanguage": "Wheat or a wheat derivative. Note this is a wheat allergy list, not a full gluten-free list — barley and rye contain gluten but not wheat protein specifically.",
        "whyForYouTemplate": "Flagged because wheat is on your allergen profile.",
    },
    # --- Soy ---
    "soy": {
        "name": "Soy",
        "aliases": [
            "soy", "soybean", "soybeans", "soya", "tofu", "edamame",
            "tamari", "tempeh", "textured vegetable protein", "tvp",
            "soy lecithin", "soy protein isolate",
        ],
        "allergen_tags": ["soy"],
        "plainLanguage": "Soybean or a soy derivative — soy lecithin (a common emulsifier) is a frequent hidden source.",
        "whyForYouTemplate": "Flagged because soy is on your allergen profile.",
    },
    # --- Sesame (added as the 9th major US allergen by the FASTER Act, 2021) ---
    "sesame": {
        "name": "Sesame",
        "aliases": [
            "sesame", "sesame seed", "sesame seeds", "sesame oil", "tahini",
            "benne", "gomasio", "sesamol", "sesamum",
        ],
        "allergen_tags": ["sesame"],
        "plainLanguage": "Sesame seed or a sesame derivative — the most recently added major US allergen (2021).",
        "whyForYouTemplate": "Flagged because sesame is on your allergen profile.",
    },
    # --- Non-allergen flags kept from the original scaffold ---
    "red40": {
        "name": "Red 40",
        "aliases": ["red 40", "fd&c red no. 40", "allura red ac", "e129"],
        "allergen_tags": [],
        "plainLanguage": "A synthetic dye made from petroleum, used to make foods look redder than the ingredients actually would on their own.",
        "whyForYouTemplate": "Flagged because it's a synthetic dye — some people react to it even without a formal allergy.",
    },
    "natural-flavor": {
        "name": "Natural Flavor",
        "aliases": ["natural flavor", "natural flavoring", "natural flavors"],
        "allergen_tags": [],
        "plainLanguage": "A catch-all term for flavor compounds from real plant/animal sources — the exact recipe isn't disclosed.",
        "whyForYouTemplate": "Flagged as 'unclear' because the exact source can't be confirmed from the label alone.",
    },
}