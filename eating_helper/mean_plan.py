from enum import Enum, unique
from functools import cached_property
from typing import Dict, List

import yaml
from beautiful_date import D, hours
from pydantic import BaseModel

from .google_api.calendar import add_event_to_meal_plan_calendar, get_calendar_service
from .recipes import Nutrition, Recipe, UntrackedIngredient
from .secrets import MEAL_PLAN_YAML_FILE_PATH


@unique
class FoodGroup(str, Enum):
    """
    Food groups I use to make it easier to shop groceries.
    """

    BREAD = "bread"
    PANTRY = "pantry"
    DAIRY = "dairy"
    FROZEN = "frozen"
    PRODUCE = "produce"
    MEAT = "meat"
    INDIAN = "indian"  # Go to an indian store
    ASIAN = "asian"  # Go to an asian store


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
    "1949692": FoodGroup.PANTRY,
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


class GroceryItem(BaseModel):
    ingredient: UntrackedIngredient
    group: FoodGroup


class Meal(BaseModel):
    recipes: List[Recipe]


class DailyMealPlan(BaseModel):
    meals: List[Meal]

    def create_calendar_events(self, is_dry_run=False) -> None:
        calendar_service = get_calendar_service()
        start = D.today()[9:00]
        for i, meal in enumerate(self.meals):
            meal_time = start + 4 * i * hours
            recipe_names = [recipe.name.title() for recipe in meal.recipes]
            print(i, meal_time, recipe_names)
            # Cook + eat every X hours. Cook + eat takes 1 hour on average.
            if not is_dry_run:
                add_event_to_meal_plan_calendar(
                    calendar_service,
                    ", ".join(recipe_names),
                    meal_time=meal_time,
                )


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
                    "Ingredient {name} has duplicate units. Not allowed for now."
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
