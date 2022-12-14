from collections import defaultdict
import requests
import requests_cache
import pprint
import yaml
import tqdm
from typing import List

import eating_helper.secrets as secrets
from eating_helper.google_api import get_google_tasks_service
from eating_helper.google_api import clear_google_tasks

DAYS_PER_WEEK = 7
USDA_URL = "https://api.nal.usda.gov/fdc/v1"
USDA_API_KEY = secrets.USDA_API_KEY
USDA_API_MAX_CHUNK_SIZE = 20

requests_cache.install_cache(
    cache_name="usda_cache",
    backend="sqlite",
)

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
}

# Some ID/names do not have groups already associated with them.
REF_TO_GROUP = {
    "black pepper": FOOD_GROUPS["pantry"],
    "cacao powder": FOOD_GROUPS["pantry"],
    "chili powder": FOOD_GROUPS["pantry"],
    "cumin": FOOD_GROUPS["pantry"],
    "garlic": FOOD_GROUPS["veg"],
    "jalapeno": FOOD_GROUPS["veg"],
    "poblano": FOOD_GROUPS["veg"],
    "lime": FOOD_GROUPS["fruit"],
    "pico de gallo": FOOD_GROUPS["veg"],
    "salt": FOOD_GROUPS["pantry"],
    "soy sauce": FOOD_GROUPS["pantry"],
    "vinegar": FOOD_GROUPS["pantry"],
    "sambal oelek": FOOD_GROUPS["pantry"],
    "chipotle in adobo sauce": FOOD_GROUPS["pantry"],
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
}


def get_foods_by_id(fdc_ids) -> List:
    # "foods" endpoint only works with abridged for some reason.
    # To get more details (like food category) you need to get food
    # individually. So, use "food" endpoint (notice no s).
    print("Getting foods by id...")
    result = []
    for fdc_id in tqdm.tqdm(fdc_ids):
        url = f"{USDA_URL}/food/{fdc_id}?api_key={USDA_API_KEY}"
        response = requests.get(url)
        result.append(response.json())

    return result


def map_fdc_ids_to_info(fdc_ids) -> dict:
    foods = get_foods_by_id(fdc_ids)
    m = {}
    for food in foods:
        m[food["fdcId"]] = {
            "name": food["description"].capitalize(),
            "group": food.get("foodCategory", {}).get("description", ""),
        }

    return m


def get_food_nutrients_by_id(fdc_ids):
    foods = get_foods_by_id(fdc_ids)
    id_to_nutrients = {}
    for food in foods:
        nutrients = food["foodNutrients"]
        relevant_nutrients = {}
        for nutrient in nutrients:
            if nutrient["nutrient"]["name"] == "Protein":
                relevant_nutrients["protein"] = (
                    nutrient["amount"],
                    nutrient["nutrient"]["unitName"],
                )
            elif (
                nutrient["nutrient"]["name"]
                in [
                    "Energy",
                    "Energy (Atwater General Factors)",
                ]
                and nutrient["nutrient"]["unitName"] == "kcal"
            ):
                relevant_nutrients["kcal"] = (
                    nutrient["amount"],
                    nutrient["nutrient"]["unitName"],
                )
        food_name = food["description"]
        if "protein" not in relevant_nutrients:
            pprint.pprint(nutrients)
            print(f"Protein not found in {food_name}")
            exit(1)
        if "kcal" not in relevant_nutrients:
            pprint.pprint(nutrients)
            print(f"kcal not found in {food_name}")
            exit(1)
        id_to_nutrients[food["fdcId"]] = relevant_nutrients
    return id_to_nutrients


def print_weekly_meal_plan_stats():
    with open("./weekly_meal_plan.yaml", "r") as f:
        meal_plan = yaml.safe_load(f)

    with open("./recipes.yaml", "r") as f:
        recipes = yaml.safe_load(f)

    kcal_per_day = [0] * DAYS_PER_WEEK
    protein_per_day = [0] * DAYS_PER_WEEK
    for meal_name in meal_plan:
        servings = recipes[meal_name]["servings"]
        multi = meal_plan[meal_name]["multiplier"]
        print(meal_name, f"({servings * multi})")
        caloric_ingredients = recipes[meal_name]["ingredients"]["main"]
        id_to_nutrients = get_food_nutrients_by_id(caloric_ingredients.keys())

        assert all([x["kcal"][1] == "kcal" for x in id_to_nutrients.values()])
        single_meal_kcal = 0
        for fdc_id in id_to_nutrients:
            kcal_per_100_grams = id_to_nutrients[fdc_id]["kcal"][0]
            single_meal_kcal += caloric_ingredients[fdc_id] * kcal_per_100_grams / 100
        single_meal_kcal /= servings
        print("kcal per serving:", round(single_meal_kcal))

        assert all([x["protein"][1] == "g" for x in id_to_nutrients.values()])
        single_meal_protein = 0
        for fdc_id in id_to_nutrients:
            protein_per_100_grams = id_to_nutrients[fdc_id]["protein"][0]
            single_meal_protein += (
                caloric_ingredients[fdc_id] * protein_per_100_grams / 100
            )
        single_meal_protein /= servings
        print("prot per serving:", round(single_meal_protein))

        days_to_eat_on = schedule_days_to_eat_meal_on(meal_plan[meal_name])
        for i in days_to_eat_on:
            kcal_per_day[i] += single_meal_kcal
            protein_per_day[i] += single_meal_protein

        print()

    meals_per_day = get_meals_per_day(meal_plan)
    for i, (kcal, prot, meals) in enumerate(zip(kcal_per_day, protein_per_day, meals_per_day)):
        kcal = round(kcal)
        prot = round(prot)
        print(i, str(kcal).ljust(8, " "), str(prot).ljust(8, " "), meals)

    print()

    print("kcal, weekly total:", round(sum(kcal_per_day)))
    print("prot, weekly total:", round(sum(protein_per_day)))


def create_weekly_meal_plan():
    service = get_google_tasks_service()
    response = (
        service.tasks().list(tasklist=secrets.GOOGLE_TASKS_MEAL_PLAN_ID).execute()
    )

    day_index_to_task = {}
    for task in response["items"]:
        print(task)
        day_index = int(task["title"])
        assert 0 <= day_index < 7
        day_index_to_task[day_index] = task

    with open("./weekly_meal_plan.yaml", "r") as f:
        meal_plan = yaml.safe_load(f)

    meals_per_day = get_meals_per_day(meal_plan)
    for i, meals in enumerate(meals_per_day):
        print(f"Adding meals to day {i}")
        for meal_name in meals:
            service.tasks().insert(
                tasklist=secrets.GOOGLE_TASKS_MEAL_PLAN_ID,
                parent=day_index_to_task[i]["id"],
                body={"title": meal_name},
            ).execute()


def get_meals_per_day(meal_plan):
    meals_per_day = [[] for _ in range(DAYS_PER_WEEK)]
    for meal_name in meal_plan:
        days_to_eat_on = schedule_days_to_eat_meal_on(meal_plan[meal_name])
        for i in days_to_eat_on:
            meals_per_day[i].append(meal_name)
    return meals_per_day


def schedule_days_to_eat_meal_on(meal):
    eating_schedule = meal["eat on"]
    days_to_eat_on = []
    for term in eating_schedule:
        if term == "daily":
            days_to_eat_on.extend(list(range(DAYS_PER_WEEK)))
        else:
            days_to_eat_on.append(term)

    return days_to_eat_on


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
        print(f"Creating parent task to contain food subtasks: {group}")
        parent_task = (
            service.tasks()
            .insert(
                tasklist=secrets.GOOGLE_TASKS_SHOPPING_LIST_ID,
                body={"title": group},
            ).execute()
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

