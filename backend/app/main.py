"""
SafeBite backend — Core Scan Flow
==================================
Endpoints your frontend (scan.html / verdict.html / ingredient-detail.html)
should call instead of the mock functions in app-data.js:

  POST /api/scan            -> upload a label photo, get back a verdict
  GET  /api/scans           -> scan history (for dashboard)
  GET  /api/scans/{id}      -> one scan, same shape as MOCK_SCANS entries
  GET  /api/ingredient/{id} -> same shape as MOCK_INGREDIENTS entries
  GET  /api/profile         -> current user's allergen profile
  POST /api/profile         -> save allergen profile
  GET  /api/swaps/{scan_id} -> ranked swap candidates for a flagged/unclear scan
  GET  /api/swaps?q=        -> ranked swap candidates for a typed/spoken craving

Response JSON shapes match app-data.js exactly on purpose, so swapping
the frontend from mock -> real is a URL change, not a rewrite.

Run:
  pip install -r requirements.txt
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import uuid, io, re

app = FastAPI(title="SafeBite API")

# Allow the static frontend (served from any origin/port during dev) to call this.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------
# "DATABASE" — in-memory for now. Swap for SQLite/Postgres later;
# nothing above this layer needs to change if you keep the shape.
# ---------------------------------------------------------------

USER_PROFILE = {
    "allergens": [],   # starts empty so first-time users hit the onboarding guard
}

SCANS_DB = {}  # scan_id -> scan dict

# Ingredient knowledge base: canonical id -> aliases + plain-language copy.
# TODO: replace with your trained captioner output; this is the rule-based
# stand-in so the verdict engine and ingredient-detail page work end-to-end today.
INGREDIENT_KB = {
    "red40": {
        "name": "Red 40",
        "aliases": ["red 40", "fd&c red no. 40", "allura red ac", "e129"],
        "allergen_tags": [],
        "plainLanguage": "A synthetic dye made from petroleum, used to make foods look redder than the ingredients actually would on their own.",
        "whyForYouTemplate": "Flagged because it's a synthetic dye — some people react to it even without a formal allergy.",
    },
    "peanut": {
        "name": "Peanut",
        "aliases": ["peanut", "peanuts", "groundnut", "arachis oil"],
        "allergen_tags": ["peanut"],
        "plainLanguage": "A legume, one of the most common food allergens.",
        "whyForYouTemplate": "Flagged because peanut is on your allergen profile.",
    },
    "milk": {
        "name": "Milk / Dairy",
        "aliases": ["milk", "dairy", "whey", "casein", "lactose"],
        "allergen_tags": ["dairy"],
        "plainLanguage": "Derived from cow's milk — includes whey and casein even when 'milk' isn't listed directly.",
        "whyForYouTemplate": "Flagged because dairy is on your allergen profile.",
    },
    "natural-flavor": {
        "name": "Natural Flavor",
        "aliases": ["natural flavor", "natural flavoring", "natural flavors"],
        "allergen_tags": [],
        "plainLanguage": "A catch-all term for flavor compounds from real plant/animal sources — the exact recipe isn't disclosed.",
        "whyForYouTemplate": "Flagged as 'unclear' because the exact source can't be confirmed from the label alone.",
    },
}


# Swap candidates. TODO: replace with the real VAE embedding search —
# this is a keyword/tag match so Swap Results + Craving Search are
# functional today instead of blocked on the model.
SWAP_DB = [
    {"id": "sw1", "name": "Sparkling Apple", "tags": ["soda", "sweet", "drink", "fizzy"],
     "macroDelta": "-12g sugar, same fizz", "why": "Same carbonated snap as soda, without the added sugar."},
    {"id": "sw2", "name": "Coconut Yogurt Bark", "tags": ["dairy", "sweet", "snack", "crunchy"],
     "macroDelta": "0g dairy, +3g fiber", "why": "Dairy-free but keeps the creamy-crunchy combo."},
    {"id": "sw3", "name": "Roasted Chickpeas", "tags": ["peanut", "salty", "snack", "crunchy"],
     "macroDelta": "+4g protein, nut-free", "why": "Same salty crunch as peanuts, without the allergen."},
    {"id": "sw4", "name": "Herb Rice Crackers", "tags": ["gluten", "salty", "snack", "crunchy"],
     "macroDelta": "0g gluten, same crunch", "why": "Gluten-free swap that keeps the crunchy-savory profile."},
    {"id": "sw5", "name": "Frozen Grapes", "tags": ["sweet", "snack", "cold", "fruity"],
     "macroDelta": "-18g sugar, all natural", "why": "Scratches the same sweet-cold itch as candy or ice cream."},
]

def rank_swaps(query_tags: List[str], limit: int = 3):
    scored = []
    for item in SWAP_DB:
        score = len(set(t.lower() for t in query_tags) & set(item["tags"]))
        scored.append((score, item))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [item for score, item in scored[:limit]]


# ---------------------------------------------------------------
# Pydantic response models — mirror app-data.js shapes
# ---------------------------------------------------------------

class FlaggedIngredient(BaseModel):
    id: str
    name: str

class ScanResult(BaseModel):
    scanId: str
    productName: str
    date: str
    verdict: str  # "safe" | "flagged" | "unclear"
    flaggedIngredients: List[FlaggedIngredient]

class IngredientDetail(BaseModel):
    name: str
    plainLanguage: str
    aliases: List[str]
    whyForYou: str

class ProfileIn(BaseModel):
    allergens: List[str]


# ---------------------------------------------------------------
# PANEL DETECTION — TODO: real YOLO/CNN detector goes here.
# For now: no-op, assumes the whole uploaded image is the panel.
# ---------------------------------------------------------------
def detect_panel(image_bytes: bytes) -> bytes:
    # TODO: run your trained detector, crop to the ingredients panel,
    # return the cropped image bytes. Returning input unchanged for now.
    return image_bytes


# ---------------------------------------------------------------
# OCR — real pytesseract call. Falls back to empty string if
# tesseract isn't installed on the machine running this.
# ---------------------------------------------------------------
def run_ocr(image_bytes: bytes) -> str:
    try:
        import pytesseract
        from PIL import Image
        img = Image.open(io.BytesIO(image_bytes))
        text = pytesseract.image_to_string(img)
        return text.lower()
    except Exception as e:
        # TODO: swap for your trained CNN/CRNN OCR model (Section 9 metrics).
        # pytesseract is just a real, working placeholder so the pipeline
        # is testable end-to-end before your custom model is ready.
        print("OCR failed/unavailable:", e)
        return ""


# ---------------------------------------------------------------
# VERDICT ENGINE — rule-based keyword matching against the user's
# allergen profile + the ingredient KB above. This is genuinely
# functional today; swap in the deterministic engine from your
# report (Section on the verdict logic) when it's ready.
# ---------------------------------------------------------------
def compute_verdict(ocr_text: str, profile_allergens: List[str]):
    flagged = []
    unclear = False

    for ing_id, ing in INGREDIENT_KB.items():
        for alias in ing["aliases"]:
            if re.search(r"\b" + re.escape(alias) + r"\b", ocr_text):
                is_profile_match = any(tag in profile_allergens for tag in ing["allergen_tags"])
                is_ambiguous = len(ing["allergen_tags"]) == 0 and ing_id == "natural-flavor"
                if is_profile_match:
                    flagged.append({"id": ing_id, "name": ing["name"]})
                elif is_ambiguous:
                    unclear = True
                break

    if flagged:
        verdict = "flagged"
    elif unclear:
        verdict = "unclear"
    else:
        verdict = "safe"

    return verdict, flagged


# ---------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------

@app.post("/api/scan", response_model=ScanResult)
async def scan_label(file: UploadFile = File(...), product_name: Optional[str] = "Scanned Product"):
    image_bytes = await file.read()

    cropped = detect_panel(image_bytes)          # TODO: real detector
    ocr_text = run_ocr(cropped)                   # real OCR (pytesseract placeholder)
    verdict, flagged = compute_verdict(ocr_text, USER_PROFILE["allergens"])

    scan_id = str(uuid.uuid4())[:8]
    scan = {
        "scanId": scan_id,
        "productName": product_name,
        "date": "today",
        "verdict": verdict,
        "flaggedIngredients": flagged,
    }
    SCANS_DB[scan_id] = scan
    return scan


@app.get("/api/scans", response_model=List[ScanResult])
def list_scans():
    return list(SCANS_DB.values())[::-1]  # most recent first


@app.get("/api/scans/{scan_id}", response_model=ScanResult)
def get_scan(scan_id: str):
    scan = SCANS_DB.get(scan_id)
    if not scan:
        raise HTTPException(404, "Scan not found")
    return scan


@app.get("/api/ingredient/{ingredient_id}", response_model=IngredientDetail)
def get_ingredient(ingredient_id: str):
    ing = INGREDIENT_KB.get(ingredient_id)
    if not ing:
        raise HTTPException(404, "Ingredient not found")
    return {
        "name": ing["name"],
        "plainLanguage": ing["plainLanguage"],
        "aliases": [a.title() for a in ing["aliases"]],
        "whyForYou": ing["whyForYouTemplate"],
    }


@app.get("/api/swaps/{scan_id}")
def get_swaps_for_scan(scan_id: str):
    scan = SCANS_DB.get(scan_id)
    if not scan:
        raise HTTPException(404, "Scan not found")
    tags = [ing["name"].lower() for ing in scan["flaggedIngredients"]] + [scan["productName"].lower()]
    # naive tag guess from product name words too, so demo scans still match something
    tags += re.findall(r"[a-z]+", scan["productName"].lower())
    return {"query": scan["productName"], "results": rank_swaps(tags)}


@app.get("/api/swaps")
def search_swaps(q: str):
    tags = re.findall(r"[a-z]+", q.lower())
    return {"query": q, "results": rank_swaps(tags)}


@app.get("/api/profile")
def get_profile():
    return USER_PROFILE


@app.post("/api/profile")
def set_profile(profile: ProfileIn):
    USER_PROFILE["allergens"] = profile.allergens
    return USER_PROFILE


@app.get("/")
def health():
    return {"status": "ok", "service": "safebite-backend"}