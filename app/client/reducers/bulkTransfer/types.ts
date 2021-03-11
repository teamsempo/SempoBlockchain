import * as React from "react";

export interface CreateBulkTransferBody {
  params?: string;
  search_string?: string;
  include_accounts?: React.Key[];
  exclude_accounts?: React.Key[];
  disbursement_amount: number;
  transfer_type?: TransferTypes
  order?: "ASC" | "DESC";
}

export interface ModifyBulkTransferBody {
  action?: "APPROVE" | "REJECT";
}

export type TransferTypes = 'DISBURSEMENT' | 'RECLAMATION' | 'BALANCE'
