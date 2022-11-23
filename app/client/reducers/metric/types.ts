export type AllowedMetricsObjects = "user" | "credit_transfer";

export interface LoadAllowedFiltersPayload {
  query?: LoadAllowedFiltersQuery;
  filterObject?: string;
}

interface LoadAllowedFiltersQuery {
  metric_type: AllowedMetricsObjects;
}

export enum MetricsActionType {
  UPDATE_METRICS = "UPDATE_METRICS",
}

export enum LoadMetricsActionType {
  LOAD_METRICS_REQUEST = "LOAD_METRICS_REQUEST",
  LOAD_METRICS_SUCCESS = "LOAD_METRICS_SUCCESS",
  LOAD_METRICS_FAILURE = "LOAD_METRICS_FAILURE",
}

export interface LoadMetricsPayload {
  path: number;
  query: object;
}

export interface DailyVolume {
  date: string;
  volume: number;
}

export interface Metrics {
  filter_active: false;
  last_day_volume: DailyVolume;
  master_wallet_balance: number;
  total_distributed: number;
  total_withdrawn: number;
  total_reclaimed: number;
}
