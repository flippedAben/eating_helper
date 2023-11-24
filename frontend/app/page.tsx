import { DefaultService } from "@/autogen/client/index"
import { startCase } from "lodash"
import { Bold } from "lucide-react"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { DataTable } from "@/components/ui/data-table"
import { RecipesNutrition, columns } from "@/components/columns"

export default async function IndexPage() {
  const weekly_data = await DefaultService.getWeeklyNutritionApiNutritionGet()
  const recipes_data = await DefaultService.getRecipesApiRecipesGet()
  const day_of_week = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
  const data: RecipesNutrition[] = [
    ...weekly_data.map((nutrition, index) => {
      return {
        name: day_of_week[(index + 5) % 7],
        ...nutrition,
      }
    }),
    ...recipes_data.map((recipe) => {
      return {
        name: startCase(recipe.name),
        ...recipe.nutrition,
      }
    }),
  ]
  const total_weekly_calories = weekly_data
    .map((a) => a.calories)
    .reduce((a, b) => a + b)
  const average_daily_calories = total_weekly_calories / 7

  return (
    <section className="container grid items-center gap-6 pb-8 pt-6 md:py-10">
      <div className="flex max-w-[980px] flex-col items-start gap-2">
        <h1 className="text-3xl leading-tight tracking-tighter md:text-4xl">
          <div className="inline font-bold">eat</div>ing{" "}
          <div className="inline font-bold">hel</div>
          per
        </h1>
        <p className="text-muted-foreground max-w-[700px] text-lg">
          Helps you eat.
        </p>
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Nutrition</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="pb-8">
            Total weekly calories: {total_weekly_calories}
          </div>
          <div className="pb-8">
            Average daily calories: {average_daily_calories}
          </div>
          <DataTable columns={columns} data={data} />
        </CardContent>
      </Card>
    </section>
  )
}
