from collections import defaultdict
from typing import List

import yaml

import eating_helper.secrets as secrets
from eating_helper.google_api.tasks import get_google_tasks_service

from .mean_plan import WeeklyMealPlan
from .recipes import Recipe, get_recipes

DAYS_PER_WEEK = 7


FOOD_GROUPS = {
    "grains": "Cereal Grains and Pasta",
    "dairy": "Dairy and Egg Products",
    "beans": "Legumes and Legume Products",
    "fruit": "Fruits and Fruit Juices",
    "nuts": "Nut and Seed Products",
    "sauce": "Soups, Sauces, and Gravies",
    "chicken": "Poultry Products",
    "veg": "Vegetables and Vegetable Products",
    "bread": "Baked Products",
    "pantry": "Pantry",
    "frozen": "Frozen",
    "indian": "Indian store",
    "seafood": "Seafood",
}

# Some ID/names do not have groups already associated with them.
# I manually associate them here.
REF_TO_GROUP = {
    1889879: FOOD_GROUPS["bread"],
    "ketchup": FOOD_GROUPS["pantry"],
    "tomato": FOOD_GROUPS["veg"],
    "cherry tomato": FOOD_GROUPS["veg"],
    "lettuce": FOOD_GROUPS["veg"],
    "cucumber": FOOD_GROUPS["veg"],
    "dill": FOOD_GROUPS["pantry"],
    2345739: FOOD_GROUPS["pantry"],
    1864648: FOOD_GROUPS["veg"],
    "bay leaf": FOOD_GROUPS["pantry"],
    2341777: FOOD_GROUPS["seafood"],
    "shallot": FOOD_GROUPS["veg"],
    "lemon": FOOD_GROUPS["fruit"],
    "parsley": FOOD_GROUPS["veg"],
    "cajun": FOOD_GROUPS["pantry"],
    "spinach": FOOD_GROUPS["veg"],
    "paprika": FOOD_GROUPS["pantry"],
    "green onion": FOOD_GROUPS["veg"],
    "onion powder": FOOD_GROUPS["pantry"],
    "garlic powder": FOOD_GROUPS["pantry"],
    "black pepper": FOOD_GROUPS["pantry"],
    "cacao powder": FOOD_GROUPS["pantry"],
    "chili powder": FOOD_GROUPS["pantry"],
    "cumin": FOOD_GROUPS["pantry"],
    "garlic": FOOD_GROUPS["veg"],
    "jalapeno": FOOD_GROUPS["veg"],
    "poblano": FOOD_GROUPS["veg"],
    "lime": FOOD_GROUPS["fruit"],
    "salsa": FOOD_GROUPS["veg"],
    "pico de gallo": FOOD_GROUPS["veg"],
    "salt": FOOD_GROUPS["pantry"],
    "sugar": FOOD_GROUPS["pantry"],
    "soy sauce": FOOD_GROUPS["pantry"],
    "five spice": FOOD_GROUPS["pantry"],
    "vinegar": FOOD_GROUPS["pantry"],
    "sambal oelek": FOOD_GROUPS["pantry"],
    "chipotle in adobo sauce": FOOD_GROUPS["pantry"],
    "water": FOOD_GROUPS["pantry"],
    "white vinegar": FOOD_GROUPS["pantry"],
    "red onion": FOOD_GROUPS["veg"],
    "cilantro": FOOD_GROUPS["veg"],
    "indian spices": FOOD_GROUPS["indian"],
    "long green chili": FOOD_GROUPS["indian"],
    "ginger garlic paste": FOOD_GROUPS["indian"],
    1859997: FOOD_GROUPS["beans"],
    1932883: FOOD_GROUPS["dairy"],
    2080001: FOOD_GROUPS["pantry"],
    2113885: FOOD_GROUPS["grains"],
    2272524: FOOD_GROUPS["frozen"],
    2273669: FOOD_GROUPS["pantry"],
    2343304: FOOD_GROUPS["bread"],
    2344719: FOOD_GROUPS["fruit"],
    386410: FOOD_GROUPS["grains"],
    562738: FOOD_GROUPS["beans"],
    577489: FOOD_GROUPS["pantry"],
    595770: FOOD_GROUPS["pantry"],
    981101: FOOD_GROUPS["grains"],
    2099245: FOOD_GROUPS["chicken"],
    2024576: FOOD_GROUPS["pantry"],
    2345725: FOOD_GROUPS["pantry"],
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
    with open("./recipes.yaml", "r") as f:
        recipes = yaml.safe_load(f)

    with open("./weekly_meal_plan.yaml", "r") as f:
        meal_plan = yaml.safe_load(f)

    grocery_list = {}
    fdc_ids = []
    for_taste_ingredients = []
    for recipe, specs in meal_plan.items():
        multiplier = specs["multiplier"]
        ingredients_in_grams = recipes[recipe]["ingredients"]["main"]
        for i, amount in ingredients_in_grams.items():
            grocery_list[i] = multiplier * amount + grocery_list.get(i, 0)
            fdc_ids.append(i)

        other_ingredients = recipes[recipe]["ingredients"]["for_taste"]
        if other_ingredients:
            for i, amount in other_ingredients.items():
                if i in grocery_list:
                    grocery_list[i].extend([amount] * multiplier)
                else:
                    for_taste_ingredients.append(i)
                    grocery_list[i] = [amount] * multiplier

    fdc_id_to_info = map_fdc_ids_to_info(fdc_ids)
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
