from collections import defaultdict
from typing import List

import eating_helper.secrets as secrets
from eating_helper.google_api.tasks import get_google_tasks_service

from .mean_plan import WeeklyMealPlan
from .recipes import Recipe, UntrackedIngredient, get_recipes


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

    ingredients = weekly_meal_plan.ingredients
    groups: Dict[FoodGroup, List[UntrackedIngredient]] = {}
    for ingredient in ingredients:
        if ingredient.group not in groups:
            groups[ingredient.group] = []

        groups[ingredient.group].append(ingredient)

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


def grocery():
    create_grocery_list()


def view():
    print_weekly_meal_plan_stats()
    create_grocery_list(is_dry_run=True)
