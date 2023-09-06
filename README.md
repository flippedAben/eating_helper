# Eating Helper

This program helps me plan eating. A lot goes into eating:

- Determine your TDEE by following a strict diet for a while and measuring body
  weight every morning.
- Use TDEE to determine how many kcal to eat.
- I favor cooking meals, which means:
  - I have recipes I want to make per day.
  - I need to go buy groceries to make these recipes.
- I need to cook/eat the meals at certain times.

How does this program help? It does a few things:

- Generates macronutrient info.
- Adds events to your Google Calendar to remind you when to eat.
- Creates a grocery list from your weekly meal plan.

There is manual effort involved. You have to create some files in order for this to work:

- `recipes.yaml`
- `weekly_meal_plan.yaml`

## Development

Run the backend server.

```shell
cd backend
poetry install
poetry run uvicorn eating_helper.web_server.main:app --reload
```

Run the frontend server.

```shell
cd frontend
npm next dev
```
