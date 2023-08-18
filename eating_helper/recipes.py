from functools import cached_property
from typing import List

from pydantic import BaseModel
from yaml import safe_load

from .secrets import RECIPES_YAML_FILE_PATH
from .usda_api import UsdaFood, get_foods_by_id


class TrackedIngredient(BaseModel):
    """
    Tracked means that I'm counting the calories/nutrition for the food.
    """

    usda_fdc_id: int
    grams: int


class UntrackedIngredient(BaseModel):
    """
    Untracked means that the ingredients is just for flavor.
    That is, I think the calories/nutrients are negligible.
    """

    name: str
    amount: float
    unit: str

    @classmethod
    def from_tracked_ingredient(
        cls,
        tracked_ingredient: TrackedIngredient,
        name=None,
    ) -> "UntrackedIngredient":
        return cls(
            name=name if name else str(tracked_ingredient.usda_fdc_id),
            amount=float(tracked_ingredient.grams),
            unit="g",
        )


class Nutrition(BaseModel):
    """
    Total nutrition for the recipe.
    All in grams, except calories, which is in kcal.
    """

    calories: int
    protein: int
    carbohydrates: int
    fat: int

    def __iadd__(self, other: "Nutrition"):
        self.calories += other.calories
        self.protein += other.protein
        self.carbohydrates += other.carbohydrates
        self.fat += other.fat
        return self

    @property
    def ratios(self) -> str:
        protein_ratio = self.protein * 4 / self.calories
        carbs_ratio = self.carbohydrates * 4 / self.calories
        fat_ratio = self.fat * 9 / self.calories
        return f"{self.calories=} {protein_ratio=} {carbs_ratio=} {fat_ratio=}"


class Recipe(BaseModel):
    name: str = ""
    tracked_ingredients: List[TrackedIngredient]
    untracked_ingredients: List[UntrackedIngredient]

    def usda_foods(self) -> List[UsdaFood]:
        fdc_ids = [ingredient.usda_fdc_id for ingredient in self.tracked_ingredients]
        usda_foods = sorted(get_foods_by_id(fdc_ids), key=lambda x: x.fdc_id)
        return usda_foods

    @cached_property
    def nutrition(self) -> Nutrition:
        usda_foods = self.usda_foods()

        calories, protein, carbohydrates, fat = [0] * 4
        for tracked_ingredient, usda_food in zip(
            sorted(self.tracked_ingredients, key=lambda x: x.usda_fdc_id), usda_foods
        ):
            ratio = tracked_ingredient.grams / 100
            calories += usda_food.calories.amount * ratio
            protein += usda_food.protein.amount * ratio
            carbohydrates += usda_food.carbohydrates.amount * ratio
            fat += usda_food.fat.amount * ratio

        return Nutrition(
            calories=round(calories),
            protein=round(protein),
            carbohydrates=round(carbohydrates),
            fat=round(fat),
        )


def get_recipes() -> List[Recipe]:
    yaml_data: dict | None = None
    with open(RECIPES_YAML_FILE_PATH, "r") as f:
        yaml_data = safe_load(f)

    recipes = []
    for name, recipe_data in yaml_data.items():
        tracked_ingredients = []
        for key, value in recipe_data["ingredients"]["main"].items():
            tracked_ingredients.append(
                TrackedIngredient(
                    usda_fdc_id=key,
                    grams=value,
                )
            )

        untracked_ingredients = []
        untracked_ingredients_raw_data = recipe_data["ingredients"]["for_taste"]
        if untracked_ingredients_raw_data:
            for key, value in untracked_ingredients_raw_data.items():
                amount, unit = value.split()
                untracked_ingredients.append(
                    UntrackedIngredient(
                        name=key,
                        amount=float(amount),
                        unit=unit,
                    )
                )

        recipes.append(
            Recipe(
                name=name,
                tracked_ingredients=tracked_ingredients,
                untracked_ingredients=untracked_ingredients,
            )
        )

    return recipes
