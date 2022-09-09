import {
  LoadMetricsActionType,
  MetricsActionType,
  Metrics,
  LoadMetricsPayload,
} from "./types";
import { ActionsUnion, createAction } from "../../reduxUtils";

export const MetricAction = {
  updateMetrics: (metrics: Metrics) =>
    createAction(MetricsActionType.UPDATE_METRICS, metrics),
};
export type MetricAction = ActionsUnion<typeof MetricAction>;

export const LoadMetricAction = {
  loadMetricRequest: (payload: LoadMetricsPayload) =>
    createAction(LoadMetricsActionType.LOAD_METRICS_REQUEST, payload),
  loadMetricSuccess: () =>
    createAction(LoadMetricsActionType.LOAD_METRICS_SUCCESS),
  loadMetricFailure: (error: string) =>
    createAction(LoadMetricsActionType.LOAD_METRICS_FAILURE, error),
};
export type LoadMetricAction = ActionsUnion<typeof LoadMetricAction>;
