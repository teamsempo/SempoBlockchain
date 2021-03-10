import * as React from "react";

export interface CreateBulkTransferBody {
  params?: string;
  search_string?: string;
  include_accounts?: React.Key[];
  exclude_accounts?: React.Key[];
  disbursement_amount: number;
  order?: "ASC" | "DESC";
}

export interface ModifyBulkTransferBody {
  action?: "APPROVE" | "REJECT";
}
