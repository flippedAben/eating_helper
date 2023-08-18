from typing import Dict, List

import eating_helper.secrets as secrets
from eating_helper.google_api.tasks import get_google_tasks_service

from .food_group import FoodGroup
from .mean_plan import WeeklyMealPlan
from .recipes import Recipe, UntrackedIngredient, get_recipes


def view():
    create_grocery_list(is_dry_run=True)

    recipes: List[Recipe] = get_recipes()
    weekly_meal_plan = WeeklyMealPlan.from_yaml_and_recipes(recipes)
    weekly_meal_plan.create_calendar_events(is_dry_run=True)

    for recipe in recipes:
        print(recipe.name)
        print(recipe.nutrition)
    print()

    for daily_plan in weekly_meal_plan.weekly_meals:
        print([recipe.name for meal in daily_plan.meals for recipe in meal.recipes])
        print(daily_plan.nutrition)
    print()

    print("total weekly nutrition")
    print(weekly_meal_plan.nutrition.ratios)


def grocery():
    create_grocery_list()


def create_grocery_list(is_dry_run=False):
    recipes: List[Recipe] = get_recipes()
    weekly_meal_plan = WeeklyMealPlan.from_yaml_and_recipes(recipes)

    grocery_items = weekly_meal_plan.grocery_items
    groups: Dict[FoodGroup, List[UntrackedIngredient]] = {}
    for item in grocery_items:
        if item.group not in groups:
            groups[item.group] = []

        groups[item.group].append(item)

    service = None
    if not is_dry_run:
        service = get_google_tasks_service()

    for group, grocery_items in groups.items():
        group = group.value.capitalize()
        print(group)
        if not is_dry_run:
            parent_task = (
                service.tasks()
                .insert(
                    tasklist=secrets.GOOGLE_TASKS_SHOPPING_LIST_ID,
                    body={"title": group},
                )
                .execute()
            )

        for item in grocery_items:
            task_title = f"{round(item.ingredient.amount)} {item.ingredient.unit} | {item.ingredient.name.capitalize()}"
            print(" " * 4, task_title)
            if not is_dry_run:
                service.tasks().insert(
                    tasklist=secrets.GOOGLE_TASKS_SHOPPING_LIST_ID,
                    body={"title": task_title},
                    parent=parent_task["id"],
                ).execute()


def calendar():
    recipes: List[Recipe] = get_recipes()
    weekly_meal_plan = WeeklyMealPlan.from_yaml_and_recipes(recipes)
    weekly_meal_plan.create_calendar_events()
