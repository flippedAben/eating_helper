from typing import Dict, List

from fastapi import FastAPI
from pydantic import BaseModel

from ..meal_plan import Nutrition, WeeklyMealPlan
from ..recipes import Recipe, get_recipes_from_yaml

app = FastAPI(
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
)


@app.get("/")
async def root() -> Dict:
    return {"hi": "test"}


@app.get("/api/nutrition")
async def get_weekly_nutrition() -> Nutrition:
    recipes: List[Recipe] = get_recipes_from_yaml()
    weekly_meal_plan = WeeklyMealPlan.from_yaml_and_recipes(recipes)
    return weekly_meal_plan.nutrition


class GetRecipesResponse(BaseModel):
    name: str
    nutrition: Nutrition


@app.get("/api/recipes")
async def get_recipes() -> List[GetRecipesResponse]:
    recipes: List[Recipe] = get_recipes_from_yaml()
    print(recipes)
    response = []
    for recipe in recipes:
        response.append(
            GetRecipesResponse(
                name=recipe.name,
                nutrition=recipe.nutrition,
            )
        )
    return response
