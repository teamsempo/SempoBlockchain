import * as React from "react";
import { RequestSortOrder } from "../../types";

export interface CreateBulkTransferBody {
  params?: string;
  label?: string;
  search_string?: string;
  include_accounts?: React.Key[];
  exclude_accounts?: React.Key[];
  disbursement_amount: number;
  transfer_type?: TransferTypes;
  order?: RequestSortOrder;
}

export interface ModifyBulkTransferBody {
  action?: "APPROVE" | "REJECT";
  notes?: string;
}

export type TransferTypes = "DISBURSEMENT" | "RECLAMATION" | "BALANCE";
