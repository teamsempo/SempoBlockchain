import { apiClient } from "./client/apiClient";
import { EditTransferCardPayload } from "../reducers/transferCard/types";

export const editTransferCardAPI = ({ body, path }: EditTransferCardPayload) =>
  apiClient({
    url: "/transfer_cards/public_serial_number/",
    method: "PUT",
    body: body,
    path: path
  });
