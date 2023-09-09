from typing import Dict, List

from fastapi import FastAPI

from ..meal_plan import Nutrition, WeeklyMealPlan
from ..recipes import Recipe, get_recipes

app = FastAPI()


@app.get("/")
async def root() -> Dict:
    return {"hi": "test"}


@app.get("/nutrition")
async def get_weekly_nutrition() -> Nutrition:
    recipes: List[Recipe] = get_recipes()
    # for recipe in recipes:
    #     print(recipe.name)
    #     print(recipe.nutrition)
    weekly_meal_plan = WeeklyMealPlan.from_yaml_and_recipes(recipes)
    return weekly_meal_plan.nutrition
