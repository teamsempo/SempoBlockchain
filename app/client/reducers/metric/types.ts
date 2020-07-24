import { inferredPredicate } from "../../../node_modules/@types/babel__traverse/node_modules/@babel/types/lib";

export interface LoadAllowedFiltersPayload {
  query?: LoadAllowedFiltersQuery;
  filterObject?: string;
}

interface LoadAllowedFiltersQuery {
  metric_type: "user" | "credit_transfer";
}

export enum MetricsActionType {
  UPDATE_METRICS = "UPDATE_METRICS"
}

export enum LoadMetricsActionType {
  LOAD_METRICS_REQUEST = "LOAD_METRICS_REQUEST",
  LOAD_METRICS_SUCCESS = "LOAD_METRICS_SUCCESS",
  LOAD_METRICS_FAILURE = "LOAD_METRICS_FAILURE"
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
  daily_disbursement_volume: DailyVolume[];
  daily_transaction_volume: DailyVolume[];
  filter_active: false;
  has_transferred_count: number;
  last_day_volume: DailyVolume;
  master_wallet_balance: number;
  total_beneficiaries: number;
  total_distributed: number;
  total_exchanged: number;
  total_spent: number;
  total_users: number;
  transfer_use_breakdown: object;
  zero_balance_count: number;
}
