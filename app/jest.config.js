// jest.config.js
const { jsWithBabel: tsjPreset } = require("ts-jest/presets");

module.exports = {
  verbose: true,
  roots: ["./client"],
  transform: {
    ...tsjPreset.transform
  },
  snapshotSerializers: ["enzyme-to-json/serializer"],
  setupFilesAfterEnv: ["./client/__tests__/setup/setupTests.js"],
  coveragePathIgnorePatterns: [
    "/node_modules/",
    "/client/__tests__/setup/setupTests.js"
  ],
  testPathIgnorePatterns: ["/node_modules/", "/client/__tests__/setup/"],
  transformIgnorePatterns: ["/node_modules/"],
  testEnvironment: "jsdom"
};
