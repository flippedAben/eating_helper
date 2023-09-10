/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CancelablePromise } from "../core/CancelablePromise"
import { OpenAPI } from "../core/OpenAPI"
import { request as __request } from "../core/request"
import type { GetRecipesResponse } from "../models/GetRecipesResponse"
import type { Nutrition } from "../models/Nutrition"

export class DefaultService {
  /**
   * Root
   * @returns any Successful Response
   * @throws ApiError
   */
  public static rootGet(): CancelablePromise<Record<string, any>> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/",
    })
  }

  /**
   * Get Weekly Nutrition
   * @returns Nutrition Successful Response
   * @throws ApiError
   */
  public static getWeeklyNutritionApiNutritionGet(): CancelablePromise<Nutrition> {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/nutrition",
    })
  }

  /**
   * Get Recipes
   * @returns GetRecipesResponse Successful Response
   * @throws ApiError
   */
  public static getRecipesApiRecipesGet(): CancelablePromise<
    Array<GetRecipesResponse>
  > {
    return __request(OpenAPI, {
      method: "GET",
      url: "/api/recipes",
    })
  }
}
