import "../../../setup/setupTests.js";
import { CreditTransfers } from "../../../../reducers/creditTransfer/types";
import { CreditTransferAction } from "../../../../reducers/creditTransfer/actions";
import { byId } from "../../../../reducers/creditTransfer/reducers";
import {
  CreditTransferData,
  AnotherCreditTransferData
} from "../../../../__fixtures__/creditTransfer/creditTransferData";

describe("byId reducer", () => {
  let updatedState: CreditTransfers;

  beforeEach(() => {
    updatedState = byId(
      {},
      CreditTransferAction.updateCreditTransferListRequest({
        "0x1234": CreditTransferData
      })
    );
  });

  it("add single creditTransfer", () => {
    expect(Object.keys(updatedState)).toHaveLength(1);
    expect(updatedState["0x1234"]).toEqual(CreditTransferData);
  });

  it("add multiple creditTransfers", () => {
    updatedState = byId(
      {},
      CreditTransferAction.updateCreditTransferListRequest({
        "0x1234": CreditTransferData,
        "0x2345": AnotherCreditTransferData
      })
    );
    expect(Object.keys(updatedState)).toHaveLength(2);
    expect(updatedState["0x2345"]).toEqual(AnotherCreditTransferData);
  });
});
