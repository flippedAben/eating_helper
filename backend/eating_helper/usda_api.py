from functools import cached_property
from typing import List

import requests
import requests_cache
from pydantic import BaseModel

from .secrets import USDA_API_KEY

USDA_URL = "https://api.nal.usda.gov/fdc/v1"
USDA_API_MAX_CHUNK_SIZE = 20

requests_cache.install_cache(
    cache_name="usda_cache",
    backend="sqlite",
)


class UsdaNutrient(BaseModel):
    name: str
    amount: float | None
    unit: str


class UsdaFood(BaseModel):
    fdc_id: int
    name: str
    group: str | None
    # each nutrient's amount is per 100g of the food.
    # Example: 13g protein per 100g of oats
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
