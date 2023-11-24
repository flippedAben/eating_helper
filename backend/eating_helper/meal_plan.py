from functools import cached_property
from typing import Dict, List

import yaml
from beautiful_date import BeautifulDate, D, days, hours
from pydantic import BaseModel

from .food_group import (
    INGREDIENT_TO_CUSTOM_FOOD_GROUP,
    USDA_TO_CUSTOM_FOOD_GROUP,
    FoodGroup,
)
from .google_api.calendar import add_event_to_meal_plan_calendar, get_calendar_service
from .recipes import Nutrition, Recipe, UntrackedIngredient
from .secrets import MEAL_PLAN_YAML_FILE_PATH


class GroceryItem(BaseModel):
    ingredient: UntrackedIngredient
    group: FoodGroup


class Meal(BaseModel):
    recipes: List[Recipe]


class DailyMealPlan(BaseModel):
    meals: List[Meal]

    def create_calendar_events(self, day: BeautifulDate, is_dry_run=False) -> None:
        calendar_service = get_calendar_service()
        for i, meal in enumerate(self.meals):
            meal_time = day + 3 * i * hours
            recipe_names = [recipe.name.title() for recipe in meal.recipes]
            # Cook + eat every X hours. Cook + eat takes 1 hour on average.
            if not is_dry_run:
                add_event_to_meal_plan_calendar(
                    calendar_service,
                    ", ".join(recipe_names),
                    meal_time=meal_time,
                )

    @cached_property
    def nutrition(self) -> Nutrition:
        daily_nutrition = Nutrition(calories=0, protein=0, carbohydrates=0, fat=0)
        for meal in self.meals:
            for recipe in meal.recipes:
                daily_nutrition += recipe.nutrition
        return daily_nutrition


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
        name_to_recipe["eat out"] = None

        weekly_meal_plan = []
        for _, meals_dict in yaml_data.items():
            meals: List[Meal] = []
            for _, recipe_names in meals_dict.items():
                recipes: List[Recipe] = []
                if recipe_names:
                    for name in recipe_names:
                        recipes.append(name_to_recipe[name])
                    meals.append(Meal(recipes=recipes))
            weekly_meal_plan.append(DailyMealPlan(meals=meals))
        return cls(weekly_meals=weekly_meal_plan)

    @cached_property
    def nutrition(self) -> Nutrition:
        weekly_nutrition = Nutrition(calories=0, protein=0, carbohydrates=0, fat=0)
        for daily_meal_plan in self.weekly_meals:
            weekly_nutrition += daily_meal_plan.nutrition

        return weekly_nutrition

    @cached_property
    def grocery_items(self) -> List[GroceryItem]:
        """
        Returns the list of items required to cook the meals for the week.
        """
        grocery_items: List[GroceryItem] = []
        for daily_meal_plan in self.weekly_meals:
            for meal in daily_meal_plan.meals:
                for recipe in meal.recipes:
                    for ingredient in recipe.untracked_ingredients:
                        try:
                            group = INGREDIENT_TO_CUSTOM_FOOD_GROUP[ingredient.name]
                        except KeyError as e:
                            print(ingredient)
                            raise e
                        grocery_items.append(
                            GroceryItem(
                                ingredient=ingredient,
                                group=group,
                            )
                        )

                    usda_id_to_food = {
                        food.fdc_id: food for food in recipe.usda_foods()
                    }
                    for ingredient in recipe.tracked_ingredients:
                        food = usda_id_to_food[ingredient.usda_fdc_id]
                        group = food.group
                        if group:
                            try:
                                group = USDA_TO_CUSTOM_FOOD_GROUP[group]
                            except KeyError as e:
                                print(ingredient, group)
                                raise e
                        else:
                            try:
                                group = INGREDIENT_TO_CUSTOM_FOOD_GROUP[
                                    str(ingredient.usda_fdc_id)
                                ]
                            except KeyError as e:
                                print(ingredient, group)
                                raise e
                        grocery_items.append(
                            GroceryItem(
                                ingredient=UntrackedIngredient.from_tracked_ingredient(
                                    ingredient,
                                    name=food.name,
                                ),
                                group=group,
                            )
                        )

        name_to_items: Dict[str, List[GroceryItem]] = {}
        for item in grocery_items:
            if item.ingredient.name not in name_to_items:
                name_to_items[item.ingredient.name] = []
            name_to_items[item.ingredient.name].append(item)

        for name, items in name_to_items.items():
            if not all(
                items[0].ingredient.unit == item.ingredient.unit for item in items
            ):
                raise Exception(
                    f"Ingredient {name} has duplicate units. Not allowed for now."
                )

        unique_grocery_items = []
        for name, items in name_to_items.items():
            total_amount = sum(item.ingredient.amount for item in items)
            unique_grocery_items.append(
                GroceryItem(
                    ingredient=UntrackedIngredient(
                        name=items[0].ingredient.name,
                        amount=total_amount,
                        unit=items[0].ingredient.unit,
                    ),
                    group=items[0].group,
                )
            )

        return unique_grocery_items

    def create_calendar_events(self, days_after: int, is_dry_run=False):
        start = D.today()[9:00] + days_after * days
        for daily_meal_plan in self.weekly_meals:
            daily_meal_plan.create_calendar_events(start, is_dry_run=is_dry_run)
            start += 1 * days
