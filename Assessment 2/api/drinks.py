import requests as req

BASE_URL = "https://www.thecocktaildb.com/api/json/v1/1"

ANIMAL_INGREDIENTS = {
    "egg", "egg white", "egg yolk", "honey",
    "milk", "cream", "half-and-half", "butter", 
    "yogurt", "clam", "clam juice", "oyster", 
    "anchovy", "fish sauce", "shrimp"
}
NON_VEGETARIAN_INGREDIENTS = {"clam", "clam juice", "oyster", "anchovy", "fish sauce", "shrimp"}
SUGAR_DRINK_BLOCKERS = {"sugar", "simple syrup", "honey", "agave", "maple syrup", "grenadine", "corn syrup"}
KETO_DRINK_BLOCKERS = SUGAR_DRINK_BLOCKERS | {"juice", "milk", "cream", "coconut cream", "sweet liqueur", "triple sec", "cola", "tonic"}
DAIRY_INGREDIENTS = {"milk", "cream", "half-and-half", "yogurt", "ice cream"}

# -----------------------------
# Core API Helper
# -----------------------------
def _fetch(endpoint):
    try:
        r = req.get(f"{BASE_URL}/{endpoint}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Drink API error:", e)
        return None

# -----------------------------
# Public API Functions
# -----------------------------
def random_drink():
    data = _fetch("random.php")
    return data["drinks"][0] if data and data["drinks"] else None

def random_non_alcoholic():
    while True:
        drink = random_drink()
        if drink and drink["strAlcoholic"] == "Non alcoholic":
            return drink

def search_drink(name: str):
    data = _fetch(f"search.php?s={name}")
    return data["drinks"] if data and data["drinks"] else []

# -----------------------------
# Ingredient Parsing
# -----------------------------
def get_ingredients(drink):
    ingredients = []
    for i in range(1, 16):
        ing = drink.get(f"strIngredient{i}")
        measure = drink.get(f"strMeasure{i}")
        if ing:
            ingredients.append(f"{measure or ''} {ing}".strip())
    return ingredients

def is_vegetarian_drink(drink):
    ingredients = " ".join(get_ingredients(drink)).lower()
    return not any(item in ingredients for item in NON_VEGETARIAN_INGREDIENTS)

def is_vegan_drink(drink):
    ingredients = " ".join(get_ingredients(drink)).lower()
    return not any(item in ingredients for item in ANIMAL_INGREDIENTS)

def is_sugar_free_drink(drink):
    ingredients = " ".join(get_ingredients(drink)).lower()
    return not any(item in ingredients for item in SUGAR_DRINK_BLOCKERS)

def is_keto_drink(drink):
    ingredients = " ".join(get_ingredients(drink)).lower()
    return not any(item in ingredients for item in KETO_DRINK_BLOCKERS)

def is_non_dairy_drink(drink):
    ingredients = " ".join(get_ingredients(drink)).lower()
    return not any(item in ingredients for item in DAIRY_INGREDIENTS)

