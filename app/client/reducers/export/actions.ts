import {
  ExportActionTypes,
  ExportPayload,
  ExportSuccessPayload
} from "./types";
import { createAction, ActionsUnion } from "../../reduxUtils";

export const ExportAction = {
  exportRequest: (payload: ExportPayload) =>
    createAction(ExportActionTypes.NEW_EXPORT_REQUEST, payload),
  exportSuccess: (payload: ExportSuccessPayload) =>
    createAction(ExportActionTypes.NEW_EXPORT_SUCCESS, payload),
  exportFailure: (error: string) =>
    createAction(ExportActionTypes.NEW_EXPORT_FAILURE, error),
  exportReset: () => createAction(ExportActionTypes.RESET_EXPORT)
};
export type ExportAction = ActionsUnion<typeof ExportAction>;
