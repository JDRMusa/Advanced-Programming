import requests as req

BASE_URL = "https://www.themealdb.com/api/json/v1/1"

MEAL_ALCOHOL_INGREDIENTS = {
    "wine", "red wine", "white wine", "sherry", "mirin", "beer"
}
HARAM_INGREDIENTS = {
    "pork", "bacon", "wine", "beer",
    "ham", "lard", "gelatin", "rum", 
    "vodka", "whiskey", "brandy"
}
KETO_BLOCKERS = {
    "sugar", "bread", "rice", "pasta", "potato", 
    "potatoes", "sweet potato", "flour", "corn", "cornmeal", 
    "lentils", "beans", "chickpeas", "oats", "oatmeal"
}
NON_VEGAN_INGREDIENTS = {
    "beef", "chicken", "pork", "lamb", "fish", "salmon", "tuna",
    "shrimp", "prawn", "anchovy", "bacon", "ham",
    "milk", "cheese", "butter", "cream", "yogurt", "ghee",
    "whey", "casein", "lactose",
    "egg", "eggs", "honey", "gelatin", "lard"
}
DAIRY_INGREDIENTS = {
    "milk", "cheese", "butter", "ghee", "yogurt",
    "cream", "whey", "casein", "lactose"
}
SUGAR_BLOCKERS =  {
    "brown sugar", "white sugar", "icing sugar","caster sugar",
    "honey", "maple syrup", "golden syrup", "corn syrup",
    "glucose", "fructose", "molasses", "condensed milk",
    "chocolate", "jam", "caramel"
}
# -----------------------------
# Core API Helper
# -----------------------------
def _fetch(endpoint):
    try:
        r = req.get(f"{BASE_URL}/{endpoint}", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("Meal API error:", e)
        return None

# -----------------------------
# Public API Functions
# -----------------------------
def random_meal():
    data = _fetch("random.php")
    return data["meals"][0] if data and data["meals"] else None

def search_meal(name: str):
    data = _fetch(f"search.php?s={name}")
    return data["meals"] if data and data["meals"] else []

def vegetarian_meals():
    data = _fetch("filter.php?c=Vegetarian")
    return data["meals"] if data else []

# -----------------------------
# Ingredient Parsing
# -----------------------------
def get_ingredients(meal):
    ingredients = []
    for i in range(1, 21):
        ing = meal.get(f"strIngredient{i}")
        measure = meal.get(f"strMeasure{i}")
        if ing:
            ingredients.append(f"{measure or ''} {ing}".strip())
    return ingredients

def is_halal(meal):
    ingredients = " ".join(get_ingredients(meal)).lower()
    return not any(item in ingredients for item in HARAM_INGREDIENTS)

def is_vegan(meal):
    ingredients = [i.lower() for i in get_ingredients(meal)]
    return not any(bad in ing for ing in ingredients for bad in NON_VEGAN_INGREDIENTS)

def is_keto(meal):
    ingredients = " ".join(get_ingredients(meal)).lower()
    return not any(item in ingredients for item in KETO_BLOCKERS)

def is_non_dairy(meal):
    ingredients = " ".join(get_ingredients(meal)).lower()
    return not any(item in ingredients for item in DAIRY_INGREDIENTS)

def is_sugar_free(meal):
    ingredients = " ".join(get_ingredients(meal)).lower()
    return not any(item in ingredients for item in SUGAR_BLOCKERS)

def is_non_alcoholic_meals(meal):
    ingredients = " ".join(get_ingredients(meal)).lower()
    return not any(item in ingredients for item in MEAL_ALCOHOL_INGREDIENTS)