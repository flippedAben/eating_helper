/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */

import type { CancelablePromise } from "../core/CancelablePromise"
import { OpenAPI } from "../core/OpenAPI"
import { request as __request } from "../core/request"
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
}
