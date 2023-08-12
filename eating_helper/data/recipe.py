from typing import List

from pydantic import BaseModel
from yaml import safe_load

from ..secrets import RECIPES_YAML_FILE_PATH


class TrackedIngredient(BaseModel):
    """
    Tracked means that I'm counting the calories/nutrition for the food.
    """

    usda_id: int = -1
    grams: int = 0


class UntrackedIngredient(BaseModel):
    """
    Untracked means that the ingredients is just for flavor.
    That is, I think the calories/nutrients are negligible.
    """

    name: str = ""
    amount: float = 0.0
    unit: str = ""


class Recipe(BaseModel):
    name: str = ""
    tracked_ingredients: List[TrackedIngredient]
    untracked_ingredients: List[UntrackedIngredient]

    @classmethod
    def from_yaml(cls, yaml_data: dict) -> "Recipe":
        return cls()


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
                    usda_id=key,
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
