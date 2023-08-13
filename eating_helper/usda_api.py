from functools import cached_property
from typing import List

import requests
import requests_cache
from pydantic import BaseModel

from .recipes import FoodGroup
from .secrets import USDA_API_KEY

USDA_URL = "https://api.nal.usda.gov/fdc/v1"
USDA_API_MAX_CHUNK_SIZE = 20

requests_cache.install_cache(
    cache_name="usda_cache",
    backend="sqlite",
)


USDA_TO_CUSTOM_FOOD_GROUP = {
    "Baked Products": FoodGroup.BREAD,
    "Cereal Grains and Pasta": FoodGroup.PANTRY,
    "Dairy and Egg Products": FoodGroup.DAIRY,
    "Frozen": FoodGroup.FROZEN,
    "Fruits and Fruit Juices": FoodGroup.PRODUCE,
    "Legumes and Legume Products": FoodGroup.PANTRY,
    "Nut and Seed Products": FoodGroup.PRODUCE,
    "Pantry": FoodGroup.PANTRY,
    "Poultry Products": FoodGroup.MEAT,
    "Seafood": FoodGroup.MEAT,
    "Soups, Sauces, and Gravies": FoodGroup.PANTRY,
    "Vegetables and Vegetable Products": FoodGroup.PRODUCE,
}

# Some ID/names do not have groups already associated with them.
# I manually associate them here.
INGREDIENT_TO_CUSTOM_FOOD_GROUP = {
    "1859997": FoodGroup.PANTRY,
    "1864648": FoodGroup.PRODUCE,
    "1889879": FoodGroup.BREAD,
    "1932883": FoodGroup.DAIRY,
    "2024576": FoodGroup.PANTRY,
    "2080001": FoodGroup.PANTRY,
    "2099245": FoodGroup.MEAT,
    "2113885": FoodGroup.PANTRY,
    "2272524": FoodGroup.FROZEN,
    "2273669": FoodGroup.PANTRY,
    "2341777": FoodGroup.MEAT,
    "2343304": FoodGroup.BREAD,
    "2344719": FoodGroup.PRODUCE,
    "2345725": FoodGroup.PANTRY,
    "2345739": FoodGroup.PANTRY,
    "386410": FoodGroup.PANTRY,
    "562738": FoodGroup.PANTRY,
    "577489": FoodGroup.PANTRY,
    "595770": FoodGroup.PANTRY,
    "981101": FoodGroup.PANTRY,
    "bay leaf": FoodGroup.PANTRY,
    "black pepper": FoodGroup.PANTRY,
    "cacao powder": FoodGroup.PANTRY,
    "cajun": FoodGroup.PANTRY,
    "cherry tomato": FoodGroup.PRODUCE,
    "chili powder": FoodGroup.PANTRY,
    "chipotle in adobo sauce": FoodGroup.PANTRY,
    "cilantro": FoodGroup.PRODUCE,
    "cucumber": FoodGroup.PRODUCE,
    "cumin": FoodGroup.PANTRY,
    "dill": FoodGroup.PANTRY,
    "five spice": FoodGroup.PANTRY,
    "garlic powder": FoodGroup.PANTRY,
    "garlic": FoodGroup.PRODUCE,
    "ginger garlic paste": FoodGroup.INDIAN,
    "green onion": FoodGroup.PRODUCE,
    "indian spices": FoodGroup.INDIAN,
    "jalapeno": FoodGroup.PRODUCE,
    "ketchup": FoodGroup.PANTRY,
    "lemon": FoodGroup.PRODUCE,
    "lettuce": FoodGroup.PRODUCE,
    "lime": FoodGroup.PRODUCE,
    "long green chili": FoodGroup.INDIAN,
    "onion powder": FoodGroup.PANTRY,
    "paprika": FoodGroup.PANTRY,
    "parsley": FoodGroup.PRODUCE,
    "pico de gallo": FoodGroup.PRODUCE,
    "poblano": FoodGroup.PRODUCE,
    "red onion": FoodGroup.PRODUCE,
    "salsa": FoodGroup.PRODUCE,
    "salt": FoodGroup.PANTRY,
    "sambal oelek": FoodGroup.PANTRY,
    "shallot": FoodGroup.PRODUCE,
    "soy sauce": FoodGroup.PANTRY,
    "spinach": FoodGroup.PRODUCE,
    "sugar": FoodGroup.PANTRY,
    "tomato": FoodGroup.PRODUCE,
    "vinegar": FoodGroup.PANTRY,
    "water": FoodGroup.PANTRY,
    "white vinegar": FoodGroup.PANTRY,
}


class UsdaNutrient(BaseModel):
    name: str
    amount: float | None
    unit: str


class UsdaFood(BaseModel):
    fdc_id: int
    name: str
    group: str | None
    # each nutrient's amount is per 100g of the food. Example: 13g protein per 100g of oats
    nutrients: List[UsdaNutrient]

    # The following are all in grams, except calories, which is in kcal.
    @cached_property
    def calories(self) -> UsdaNutrient | None:
        for nutrient in self.nutrients:
            if (
                nutrient.name in ["Energy", "Energy (Atwater General Factors)"]
                and nutrient.unit == "kcal"
            ):
                return nutrient
        return None

    @cached_property
    def protein(self) -> UsdaNutrient | None:
        for nutrient in self.nutrients:
            if nutrient.name == "Protein":
                return nutrient
        return None

    @cached_property
    def carbohydrates(self) -> UsdaNutrient | None:
        for nutrient in self.nutrients:
            if nutrient.name == "Carbohydrate, by difference":
                return nutrient
        return None

    @cached_property
    def fat(self) -> UsdaNutrient | None:
        for nutrient in self.nutrients:
            if nutrient.name == "Total lipid (fat)":
                return nutrient
        return None


def get_foods_by_id(fdc_ids: List[int]) -> List[UsdaFood]:
    # "foods" endpoint only works with abridged for some reason.
    # To get more details (like food category) you need to get food
    # individually. So, use "food" endpoint (notice no s).
    usda_foods = []
    for fdc_id in fdc_ids:
        url = f"{USDA_URL}/food/{fdc_id}?api_key={USDA_API_KEY}"
        food = requests.get(url).json()
        usda_nutrients = []
        for nutrient in food["foodNutrients"]:
            usda_nutrients.append(
                UsdaNutrient(
                    name=nutrient["nutrient"]["name"],
                    amount=nutrient.get("amount"),
                    unit=nutrient["nutrient"]["unitName"],
                )
            )

        usda_foods.append(
            UsdaFood(
                fdc_id=fdc_id,
                name=food["description"].capitalize(),
                group=food.get("foodCategory", {}).get("description"),
                nutrients=usda_nutrients,
            )
        )

    return usda_foods
