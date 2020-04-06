import "./setup/setupTests";
import * as utils from "../utils";

describe("test formatMoney", () => {
  it.each([
    [200, undefined, undefined, undefined, "AUD", "200.00 AUD"],
    [-200, undefined, undefined, undefined, "AUD", "-200.00 AUD"],
    [undefined, undefined, undefined, undefined, "AUD", "0.00 AUD"],
    [2, 1, undefined, undefined, "USD", "2.0 USD"],
    [999999, 4, ".", ",", "R", "999,999.0000 R"]
  ])(
    ".formatMoney(%i, %i, %s, %s, %s) == %s",
    (amount, decimalCount, decimal, thousands, currency, expected) => {
      expect(
        utils.formatMoney(amount, decimalCount, decimal, thousands, currency)
      ).toBe(expected);
    }
  );
});

describe("test URL functions", () => {
  test("test parseQuery", () => {
    expect(utils.parseQuery("?is_deleted=true&foo=bar")).toStrictEqual({
      foo: "bar",
      is_deleted: "true"
    });
  });

  test("test generateFormattedURL", () => {
    expect(
      utils.generateFormattedURL("/user/", { is_deleted: true, foo: "bar" }, 1)
    ).toBe("/api/v1/user/?is_deleted=true&foo=bar");
  });
});

describe("test localStorage", () => {
  test("test setOrgId", () => {
    utils.storeOrgid("1");
    expect(localStorage).toHaveProperty("orgId", "1");
  });

  test("test getOrgId", () => {
    expect(utils.getOrgId()).toEqual("1");
  });

  test("test removeOrgId", () => {
    utils.removeOrgId("1");
    expect(localStorage).not.toHaveProperty("orgId", "1");
  });
});

test("replaceUnderscores", () => {
  expect(utils.replaceUnderscores("Hello_World")).toBe("Hello World");
});

test("replaceSpaces", () => {
  expect(utils.replaceSpaces("Hello World")).toBe("Hello-World");
});
