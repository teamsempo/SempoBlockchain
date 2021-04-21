import "../setup/setupTests";
import * as utils from "../../utils";

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

  test("test generateFormattedURLPath", () => {
    expect(
      utils.generateFormattedURLPath(
        "/user/",
        { is_deleted: true, foo: "bar" },
        1
      )
    ).toBe("/api/v1/user/?is_deleted=true&foo=bar");
  });

  test("test generateFormattedURL", () => {
    expect(
      utils.generateFormattedURL("/user/", { is_deleted: true, foo: "bar" }, 1)
    ).toBe("http://localhost/api/v1/user/?is_deleted=true&foo=bar");
  });
});

describe("test localStorage", () => {
  const orgId = "1";
  const TFAToken = "abcdadsf123123123";
  const sessionToken = "asfdasfd91234pfa";

  describe("orgId", () => {
    test("test setOrgIds", () => {
      utils.storeOrgIds(orgId);
      expect(localStorage).toHaveProperty("orgIds", orgId);
    });

    test("test getOrgIds", () => {
      expect(utils.getOrgIds()).toEqual(orgId);
    });

    test("test removeOrgIds", () => {
      utils.removeOrgIds();
      expect(localStorage).not.toHaveProperty("orgIds", orgId);
    });
  });

  describe("TFAToken", () => {
    test("test storeTFAToken", () => {
      utils.storeTFAToken(TFAToken);
      expect(localStorage).toHaveProperty("TFAToken", TFAToken);
    });

    test("test getTFAToken", () => {
      expect(utils.getTFAToken()).toEqual(TFAToken);
    });

    test("test removeTFAToken", () => {
      utils.removeTFAToken();
      expect(localStorage).not.toHaveProperty("TFAToken", TFAToken);
    });
  });

  describe("sessionToken", () => {
    test("test storeSessionToken", () => {
      utils.storeSessionToken(sessionToken);
      expect(localStorage).toHaveProperty("sessionToken", sessionToken);
    });

    test("test getToken - sessionToken only", () => {
      expect(utils.getToken()).toEqual(sessionToken);
    });

    test("test getToken - sessionToken + TFAToken", () => {
      utils.storeTFAToken(TFAToken);
      expect(utils.getToken()).toEqual(sessionToken + "|" + TFAToken);
      utils.removeTFAToken();
    });

    test("test removeSessionToken", () => {
      utils.removeSessionToken();
      expect(localStorage).not.toHaveProperty("sessionToken", sessionToken);
    });
  });
});

test("replaceUnderscores", () => {
  expect(utils.replaceUnderscores("Hello_World")).toBe("Hello World");
});

test("replaceSpaces", () => {
  expect(utils.replaceSpaces("Hello World")).toBe("Hello-World");
});

test("toTitleCase", () => {
  expect(utils.toTitleCase("hello world")).toBe("Hello World");
});

test("hexToRgb", () => {
  expect(utils.hexToRgb("#30a4a6")).toStrictEqual({ r: 48, g: 164, b: 166 });
});

test("get_zero_filled_values", () => {
  const value_array = [
    { date: "2020-07-03T00:00:00", value: 11 },
    {
      date: "2020-07-05T00:00:00",
      value: 1
    },
    { date: "2020-07-08T00:00:00", value: 1 }
  ];
  const date_values = [
    "2020-07-03T00:00:00",
    "2020-07-04T00:00:00",
    "2020-07-05T00:00:00",
    "2020-07-06T00:00:00",
    "2020-07-07T00:00:00",
    "2020-07-08T00:00:00"
  ];
  const date_array = date_values.map(date => new Date(date));
  expect(
    utils.get_zero_filled_values("value", value_array, date_array)
  ).toStrictEqual([11, 0, 1, 0, 0, 1]);
});
