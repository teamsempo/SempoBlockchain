import "../../setup/setupTests";
import { apiClient } from "../../../api/client/apiClient";

describe("test sempo apiClient", () => {
  beforeEach(() => {
    fetch.resetMocks();
  });

  it.each(["PUT", "POST", "GET", "DELETE"])(
    "%s method doesn't raise error",
    async method => {
      fetch.mockResponse(200);
      expect(apiClient({ url: "/test/", method: method })).toMatchObject({});
    }
  );

  test("BANANA method raises error", () => {
    expect(() => apiClient({ url: "/test/", method: "BANANA" })).toThrow(
      "Method provided is not supported"
    );
  });

  test("failed fetch", async () => {
    let fakeError = new Error("fake error message");
    fetch.mockReject(fakeError);

    async function failedRequest() {
      await apiClient({ url: "/test/", method: "GET" });
    }

    await expect(failedRequest()).rejects.toThrow(fakeError);
  });

  test("standard fetch returns data", async () => {
    let data = { data: "1234" };
    fetch.mockResponse(JSON.stringify(data));
    expect(await apiClient({ url: "/test/", method: "GET" })).toStrictEqual(
      data
    );
  });
});
