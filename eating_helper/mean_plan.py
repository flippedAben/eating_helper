from functools import cached_property
from typing import Dict, List

import yaml
from pydantic import BaseModel

from .recipes import Nutrition, Recipe
from .secrets import MEAL_PLAN_YAML_FILE_PATH


class Meal(BaseModel):
    recipes: List[Recipe]


class DailyMealPlan(BaseModel):
    meals: List[Meal]


class WeeklyMealPlan(BaseModel):
    weekly_meals: List[DailyMealPlan]

    class Config:
        frozen = True

    @classmethod
    def from_yaml_and_recipes(cls, recipes: List[Recipe]) -> "WeeklyMealPlan":
        yaml_data = None
        with open(MEAL_PLAN_YAML_FILE_PATH, "r") as f:
            yaml_data = yaml.safe_load(f)

        name_to_recipe = {recipe.name: recipe for recipe in recipes}

        weekly_meal_plan = []
        for _, meals_dict in yaml_data.items():
            meals: List[Meal] = []
            for _, recipe_names in meals_dict.items():
                recipes: List[Recipe] = []
                for name in recipe_names:
                    recipes.append(name_to_recipe[name])
                meals.append(Meal(recipes=recipes))
            weekly_meal_plan.append(DailyMealPlan(meals=meals))
        return cls(weekly_meals=weekly_meal_plan)

    @cached_property
    def nutrition(self) -> Nutrition:
        weekly_nutrition = Nutrition(calories=0, protein=0, carbohydrates=0, fat=0)
        for daily_meal_plan in self.weekly_meals:
            for meal in daily_meal_plan.meals:
                for recipe in meal.recipes:
                    weekly_nutrition += recipe.nutrition

        return weekly_nutrition
