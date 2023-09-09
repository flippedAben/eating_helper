/* generated using openapi-typescript-codegen -- do no edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { Nutrition } from '../models/Nutrition';

import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';

export class DefaultService {

    /**
     * Root
     * @returns any Successful Response
     * @throws ApiError
     */
    public static rootGet(): CancelablePromise<Record<string, any>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/',
        });
    }

    /**
     * Get Weekly Nutrition
     * @returns Nutrition Successful Response
     * @throws ApiError
     */
    public static getWeeklyNutritionNutritionGet(): CancelablePromise<Nutrition> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/nutrition',
        });
    }

}
