import { CreditTransfer } from "../../reducers/creditTransfer/types";

export const CreditTransferData: CreditTransfer = {
  transfer_subtype: "DISBURSEMENT", // or RECLAMATON
  transfer_type: "DISBURSEMENT" // or RECLAMATON
};

export const AnotherCreditTransferData: CreditTransfer = {
  transfer_subtype: "RECLAMATON",
  transfer_type: "RECLAMATION"
};
