# Eating Helper

This program helps me plan eating. A lot goes into eating:

- Determine your TDEE by following a strict diet for a while and measuring body
  weight every morning.
- Use TDEE to determine how many kcal to eat.
- I favor cooking meals, which means:
  - I have recipes I want to make per day.
  - I need to go buy groceries to make these recipes.
- I need to cook the meals at certain times.

## Development

Run the backend server.

```shell
poetry run uvicorn eating_helper.web_server.main:app --reload
```

Run the frontend server.

```shell
npx next dev
```
