import { DefaultService } from "@/autogen/client/index"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

export default async function IndexPage() {
  const data = await DefaultService.getWeeklyNutritionApiNutritionGet()
  console.log(data)

  return (
    <section className="container grid items-center gap-6 pb-8 pt-6 md:py-10">
      <div className="flex max-w-[980px] flex-col items-start gap-2">
        <h1 className="text-3xl leading-tight tracking-tighter md:text-4xl">
          <div className="inline font-bold">eat</div>ing{" "}
          <div className="inline font-bold">hel</div>
          per
        </h1>
        <p className="max-w-[700px] text-lg text-muted-foreground">
          Helps you eat.
        </p>
      </div>
      <Card className="w-1/2">
        <CardHeader>
          <CardTitle>Weekly nutrition</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Item</TableHead>
                <TableHead>Amount Per Week</TableHead>
                <TableHead>Average Per Day</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {Object.entries(data).map(([key, value]) => (
                <TableRow>
                  <TableCell>{key}</TableCell>
                  <TableCell>{value}</TableCell>
                  <TableCell>{Math.round(value / 7)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </section>
  )
}
