import requests
import requests_cache
import pprint
import yaml
from typing import List

import eating_helper.secrets as secrets
from eating_helper.google_api import get_google_tasks_service
from eating_helper.google_api import clear_google_tasks

DAYS_PER_WEEK = 7
USDA_URL = "https://api.nal.usda.gov/fdc/v1"
USDA_API_KEY = secrets.USDA_API_KEY
USDA_API_MAX_CHUNK_SIZE = 20

# Assumes you have my system of Syncthing + Obsidian setup
OBSIDIAN_PATH = "/home/ben/syncthing/Obsidian Vault/main"

requests_cache.install_cache(
    cache_name="usda_cache",
    backend="sqlite",
)


def search_food_raw(query, foundation_only=True) -> dict:
    url = f"{USDA_URL}/foods/search?query={query}&api_key={USDA_API_KEY}"
    if foundation_only:
        url += "&dataType=Foundation"
    response = requests.get(url)
    return response.json()


def search_food(query, foundation_only=True) -> dict:
    data = search_food_raw(query, foundation_only)
    return data["foods"]


def print_searched_foods(query, foundation_only=True):
    foods = search_food(query, foundation_only)
    for food in foods:
        print(food["fdcId"])
        print(food["description"])
        print(food["foodCategory"])
        nutrients = food["foodNutrients"]
        relevant_nutrients = [
            (
                nutrient["nutrientNumber"],
                nutrient["nutrientName"],
                nutrient["value"],
                nutrient["unitName"],
            )
            for nutrient in nutrients
            if nutrient["nutrientName"] == "Protein"
            or nutrient["nutrientName"]
            in [
                "Energy",
                "Energy (Atwater General Factors)",
            ]
            and nutrient["unitName"] == "KCAL"
        ]
        print(relevant_nutrients)
        print()


def get_foods_by_id(fdc_ids, abridged=False) -> List:
    result = []
    # "foods" endpoint only works with abridged for some reason.
    # To get more details (like food category) you need to get food
    # individually.
    if abridged:
        chunks = [
            fdc_ids[i:i + USDA_API_MAX_CHUNK_SIZE]
            for i in range(0, len(fdc_ids), USDA_API_MAX_CHUNK_SIZE)
        ]

        for ids in chunks:
            ids_str = ",".join([str(i) for i in ids])
            url = (
                f"{USDA_URL}/foods?api_key={USDA_API_KEY}&format=abridged&fdcIds={ids_str}"
            )
            response = requests.get(url)
            result.extend(response.json())
    else:
        for fdc_id in fdc_ids:
            print(f"GET {fdc_id}")
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
            if nutrient["name"] == "Protein":
                relevant_nutrients["protein"] = (
                    nutrient["amount"],
                    nutrient["unitName"],
                )
            elif (
                nutrient["name"]
                in [
                    "Energy",
                    "Energy (Atwater General Factors)",
                ]
                and nutrient["unitName"] == "KCAL"
            ):
                relevant_nutrients["kcal"] = (nutrient["amount"], nutrient["unitName"])
        id_to_nutrients[food["fdcId"]] = relevant_nutrients
    return id_to_nutrients


def print_weekly_meal_plan_stats():
    with open("./weekly_meal_plan.yaml", "r") as f:
        meal_plan = yaml.safe_load(f)

    with open("./recipes.yaml", "r") as f:
        recipes = yaml.safe_load(f)

    kcal_per_day = [0] * DAYS_PER_WEEK
    protein_per_day = [0] * DAYS_PER_WEEK
    for meal in meal_plan:
        servings = recipes[meal]["servings"]
        multi = meal_plan[meal]["multiplier"]
        print(meal, f"({servings * multi})")
        caloric_ingredients = recipes[meal]["ingredients"]["main"]
        id_to_nutrients = get_food_nutrients_by_id(caloric_ingredients.keys())

        assert all([x["kcal"][1] == "KCAL" for x in id_to_nutrients.values()])
        single_meal_kcal = 0
        for fdc_id in id_to_nutrients:
            kcal_per_100_grams = id_to_nutrients[fdc_id]["kcal"][0]
            single_meal_kcal += caloric_ingredients[fdc_id] * kcal_per_100_grams / 100
        single_meal_kcal /= servings
        print("kcal per serving:", round(single_meal_kcal))

        assert all([x["protein"][1] == "G" for x in id_to_nutrients.values()])
        single_meal_protein = 0
        for fdc_id in id_to_nutrients:
            protein_per_100_grams = id_to_nutrients[fdc_id]["protein"][0]
            single_meal_protein += (
                caloric_ingredients[fdc_id] * protein_per_100_grams / 100
            )
        single_meal_protein /= servings
        print("prot per serving:", round(single_meal_protein))

        print()

    print("kcal per day:", [round(x) for x in kcal_per_day])
    print("prot per day:", [round(x) for x in protein_per_day])
    print()

    print("kcal, weekly total:", round(sum(kcal_per_day)))
    print("prot, weekly total:", round(sum(protein_per_day)))


def create_weekly_meal_plan():
    with open("./weekly_meal_plan.yaml", "r") as f:
        meal_plan = yaml.safe_load(f)

    meals_per_day = [[] for _ in range(DAYS_PER_WEEK)]
    for meal in meal_plan:
        eating_schedule = meal_plan[meal]["eat on"]
        days_to_eat_on = []
        for term in eating_schedule:
            if term == "daily":
                days_to_eat_on.extend(list(range(DAYS_PER_WEEK)))
            else:
                days_to_eat_on.append(term)

        for i in days_to_eat_on:
            meals_per_day[i].append(meal)

    with open(OBSIDIAN_PATH + "/Meal plan.md", "w") as f:
        for i, meals in enumerate(meals_per_day):
            f.write(f"# Day {i}\n")
            for meal in meals:
                f.write(f"- [ ] {meal}\n")


def create_grocery_list():
    with open("./recipes.yaml", "r") as f:
        recipes = yaml.safe_load(f)

    with open("./weekly_meal_plan.yaml", "r") as f:
        meal_plan = yaml.safe_load(f)

    grocery_list = {}
    fdc_ids = []
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
                    grocery_list[i] = [amount] * multiplier

    fdc_id_to_info = map_fdc_ids_to_info(fdc_ids)
    service = get_google_tasks_service()
    for i, amount in grocery_list.items():
        name = fdc_id_to_info[i]["name"] if isinstance(i, int) else i 
        print(f"Adding to list: {name}")

        description = ""
        if isinstance(amount, int):
            description = f"{amount} g"
        else:
            description = " + ".join(amount)

        try:
            service.tasks().insert(
                tasklist=secrets.GOOGLE_TASKS_SHOPPING_LIST_ID,
                body={
                    "title": f"{name} | {description}"
                },
            ).execute()
        except requests.exceptions.HTTPError as e:
            print(e)
            raise e


def main():
    # print_weekly_meal_plan_stats()
    # create_weekly_meal_plan()

    create_grocery_list()
    # clear_google_tasks(secrets.GOOGLE_TASKS_SHOPPING_LIST_ID)
