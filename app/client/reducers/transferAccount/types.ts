//todo: complete when transfer account reducer converted to typescript
interface TransferAccount {}

export interface TransferAccountByIDs {
  [key: number]: TransferAccount;
}

export interface SingularTransferAccountData {
  transfer_account: string;
}

export interface MultipleTransferAccountData {
  transfer_accounts: string[];
}

export type TransferAccountData =
  | SingularTransferAccountData
  | MultipleTransferAccountData;
