from collections import defaultdict
from enum import Enum, unique
from typing import List

import yaml

import eating_helper.secrets as secrets
from eating_helper.google_api.tasks import get_google_tasks_service

from .mean_plan import WeeklyMealPlan
from .recipes import Recipe, get_recipes

DAYS_PER_WEEK = 7


@unique
class FoodGroups(str, Enum):
    BREAD = "bread"
    PANTRY = "pantry"
    DAIRY = "dairy"
    FROZEN = "frozen"
    PRODUCE = "produce"
    MEAT = "meat"
    INDIAN = "indian"  #  Go to an indian store
    ASIAN = "asian"  #  Go to an asian store


USDA_TO_MY_FOOD_GROUPS = {
    "Baked Products": FoodGroups.BREAD,
    "Cereal Grains and Pasta": FoodGroups.PANTRY,
    "Dairy and Egg Products": FoodGroups.DAIRY,
    "Frozen": FoodGroups.FROZEN,
    "Fruits and Fruit Juices": FoodGroups.PRODUCE,
    "Legumes and Legume Products": FoodGroups.PANTRY,
    "Nut and Seed Products": FoodGroups.PRODUCE,
    "Pantry": FoodGroups.PANTRY,
    "Poultry Products": FoodGroups.MEAT,
    "Seafood": FoodGroups.MEAT,
    "Soups, Sauces, and Gravies": FoodGroups.PANTRY,
    "Vegetables and Vegetable Products": FoodGroups.PRODUCE,
}

# Some ID/names do not have groups already associated with them.
# I manually associate them here.
REF_TO_GROUP = {
    "1859997": FoodGroups.PANTRY,
    "1864648": FoodGroups.PRODUCE,
    "1889879": FoodGroups.BREAD,
    "1932883": FoodGroups.DAIRY,
    "2024576": FoodGroups.PANTRY,
    "2080001": FoodGroups.PANTRY,
    "2099245": FoodGroups.MEAT,
    "2113885": FoodGroups.PANTRY,
    "2272524": FoodGroups.FROZEN,
    "2273669": FoodGroups.PANTRY,
    "2341777": FoodGroups.MEAT,
    "2343304": FoodGroups.BREAD,
    "2344719": FoodGroups.PRODUCE,
    "2345725": FoodGroups.PANTRY,
    "2345739": FoodGroups.PANTRY,
    "386410": FoodGroups.PANTRY,
    "562738": FoodGroups.PANTRY,
    "577489": FoodGroups.PANTRY,
    "595770": FoodGroups.PANTRY,
    "981101": FoodGroups.PANTRY,
    "bay leaf": FoodGroups.PANTRY,
    "black pepper": FoodGroups.PANTRY,
    "cacao powder": FoodGroups.PANTRY,
    "cajun": FoodGroups.PANTRY,
    "cherry tomato": FoodGroups.PRODUCE,
    "chili powder": FoodGroups.PANTRY,
    "chipotle in adobo sauce": FoodGroups.PANTRY,
    "cilantro": FoodGroups.PRODUCE,
    "cucumber": FoodGroups.PRODUCE,
    "cumin": FoodGroups.PANTRY,
    "dill": FoodGroups.PANTRY,
    "five spice": FoodGroups.PANTRY,
    "garlic powder": FoodGroups.PANTRY,
    "garlic": FoodGroups.PRODUCE,
    "ginger garlic paste": FoodGroups.INDIAN,
    "green onion": FoodGroups.PRODUCE,
    "indian spices": FoodGroups.INDIAN,
    "jalapeno": FoodGroups.PRODUCE,
    "ketchup": FoodGroups.PANTRY,
    "lemon": FoodGroups.PRODUCE,
    "lettuce": FoodGroups.PRODUCE,
    "lime": FoodGroups.PRODUCE,
    "long green chili": FoodGroups.INDIAN,
    "onion powder": FoodGroups.PANTRY,
    "paprika": FoodGroups.PANTRY,
    "parsley": FoodGroups.PRODUCE,
    "pico de gallo": FoodGroups.PRODUCE,
    "poblano": FoodGroups.PRODUCE,
    "red onion": FoodGroups.PRODUCE,
    "salsa": FoodGroups.PRODUCE,
    "salt": FoodGroups.PANTRY,
    "sambal oelek": FoodGroups.PANTRY,
    "shallot": FoodGroups.PRODUCE,
    "soy sauce": FoodGroups.PANTRY,
    "spinach": FoodGroups.PRODUCE,
    "sugar": FoodGroups.PANTRY,
    "tomato": FoodGroups.PRODUCE,
    "vinegar": FoodGroups.PANTRY,
    "water": FoodGroups.PANTRY,
    "white vinegar": FoodGroups.PANTRY,
}


def print_weekly_meal_plan_stats():
    recipes: List[Recipe] = get_recipes()
    for recipe in recipes:
        print(recipe.name)
        print(recipe.nutrition)
    weekly_meal_plan = WeeklyMealPlan.from_yaml_and_recipes(recipes)
    print("total weekly nutrition")
    print(weekly_meal_plan.nutrition)


def create_grocery_list(is_dry_run=False):
    recipes: List[Recipe] = get_recipes()
    weekly_meal_plan = WeeklyMealPlan.from_yaml_and_recipes(recipes)
    weekly_meal_plan.ingredients

    groups = group_foods(fdc_id_to_info, for_taste_ingredients)

    actual_groups = {}
    for group, fdc_ids in groups.items():
        actual_groups[group] = []

        for i in fdc_ids:
            name = fdc_id_to_info[i]["name"] if isinstance(i, int) else i

            amount = grocery_list[i]
            description = None
            if isinstance(amount, int):
                description = f"{amount} g"
            else:
                unit_to_value = defaultdict(int)
                for subamount in amount:
                    value, unit = subamount.split(" ")
                    value = int(value)
                    unit_to_value[unit] += value
                description = " + ".join(
                    f"{value} {unit}" for unit, value in unit_to_value.items()
                )

            actual_groups[group].append((name, description))

    if is_dry_run:
        return

    service = get_google_tasks_service()
    for group, foods in actual_groups.items():
        print(group)
        parent_task = (
            service.tasks()
            .insert(
                tasklist=secrets.GOOGLE_TASKS_SHOPPING_LIST_ID,
                body={"title": group},
            )
            .execute()
        )

        for name, description in foods:
            print(" " * 4, " | ".join([name, description]))
            service.tasks().insert(
                tasklist=secrets.GOOGLE_TASKS_SHOPPING_LIST_ID,
                body={"title": f"{name} | {description}"},
                parent=parent_task["id"],
            ).execute()


def group_foods(fdc_id_to_info, for_taste_ingredients):
    groups = defaultdict(list)
    ungrouped_ingredients = []
    for i, info in fdc_id_to_info.items():
        group = info["group"]
        if group:
            groups[group].append(i)
        else:
            if i in REF_TO_GROUP:
                group = REF_TO_GROUP[i]
                groups[group].append(i)
            else:
                ungrouped_ingredients.append(i)

    for name in for_taste_ingredients:
        if name in REF_TO_GROUP:
            group = REF_TO_GROUP[name]
            groups[group].append(name)
        else:
            ungrouped_ingredients.append(name)

    if ungrouped_ingredients:
        for i in ungrouped_ingredients:
            if isinstance(i, int):
                name = fdc_id_to_info[i]["name"]
                print(f'    {i}: FOOD_GROUPS["{name}"],')
            else:
                print(f'    "{i}": FOOD_GROUPS[""],')
        raise Exception("Ungrouped ingredients")

    return groups


def grocery():
    create_grocery_list()


def view():
    print_weekly_meal_plan_stats()
    create_grocery_list(is_dry_run=True)
