from typing import Dict, List

from fastapi import FastAPI

from ..mean_plan import WeeklyMealPlan
from ..recipes import Recipe, get_recipes

app = FastAPI()


@app.get("/")
async def root() -> Dict:
    recipes: List[Recipe] = get_recipes()
    # for recipe in recipes:
    #     print(recipe.name)
    #     print(recipe.nutrition)
    weekly_meal_plan = WeeklyMealPlan.from_yaml_and_recipes(recipes)
    return {"total_weekly_nutrition": weekly_meal_plan.nutrition}
