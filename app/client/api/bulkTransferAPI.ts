import { apiClient } from "./client/apiClient";

import {
  CreateBulkTransferPayload,
  LoadBulkTransferPayload
} from "../reducers/bulkTransfer/types";

export const loadBulkTransfersAPI = ({
  query,
  path
}: LoadBulkTransferPayload) =>
  apiClient({
    url: "/disbursement/",
    method: "GET",
    query: query,
    path: path
  });

export const newBulkTransferAPI = ({ body }: CreateBulkTransferPayload) =>
  apiClient({ url: "/disbursement/", method: "POST", body: body });
