import "./setup/setupTests";
import * as utils from "../utils";

describe("Test Utils.js File", () => {
  test("formatMoney", () => {
    expect(utils.formatMoney(10, undefined, undefined, undefined, "AUD")).toBe(
      "10.00 AUD"
    );
  });
});

// describe('test formatMoney', () => {
//   it.each`
//     amount  | decimalCount  | currency  | result
//     ${200}  | ${2}          | AUD       |
//     ${20}   | ${30}         | USD       | ${50}
//     ${-2}   | ${-3}         | R         | ${-5}
//   `('should return $result when $a and $b are used', ({amount, decimalCount, currency, result}) => {
//     expect(formatMoney(amount, decimalCount, currency)).toEqual(result);
//   });
// });
