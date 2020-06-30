import {
  DisbursementCreditTransfer,
  ReclamationCreditTransfer
} from "../../reducers/creditTransfer/types";

export const CreditTransferData: DisbursementCreditTransfer = {
  transfer_subtype: "DISBURSEMENT", // or RECLAMATON
  transfer_type: "DISBURSEMENT", // or RECLAMATON,
  transfer_amount: 10,
  transfer_status: "PENDING",
  recipient_transfer_account: { id: "fakeID" }
};

export const AnotherCreditTransferData: ReclamationCreditTransfer = {
  transfer_subtype: "RECLAMATON",
  transfer_type: "RECLAMATION",
  transfer_amount: 10,
  transfer_status: "COMPLETE",
  sender_transfer_account: { id: "fakeID" }
};
