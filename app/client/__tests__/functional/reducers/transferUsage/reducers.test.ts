import "../../../setup/setupTests.js";
import { transferUsages } from "../../../../reducers/transferUsage/reducers";
import { TransferUsage } from "../../../../reducers/transferUsage/types";
import {
  TransferData,
  AnotherTransferData
} from "../../../../__fixtures__/transfer/transferData";
import { TransferUsageAction } from "../../../../reducers/transferUsage/actions";

describe("transferUsage reducer", () => {
  let updatedState: TransferUsage[];

  beforeEach(() => {
    updatedState = transferUsages(
      [],
      TransferUsageAction.updateTransferUsages([TransferData])
    );
  });

  it("add single transferUsage", () => {
    expect(updatedState).toHaveLength(1);
    expect(updatedState).toEqual([TransferData]);
  });

  it("add multiple transferUsages", () => {
    const secondMessageState = transferUsages(
      updatedState,
      TransferUsageAction.updateTransferUsages([
        TransferData,
        AnotherTransferData
      ])
    );
    expect(secondMessageState).toHaveLength(2);
  });
});
