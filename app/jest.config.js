// jest.config.js
module.exports = {
  verbose: true,
  roots: [
    "./client"
  ],
  transform: {
    "^.+\\.[t|j]sx?$": "babel-jest"
  },
  snapshotSerializers: [
    "enzyme-to-json/serializer"
  ],
  setupFilesAfterEnv: [
    "./client/__tests__/setup/setupTests.js"
  ],
  coveragePathIgnorePatterns: [
    "/node_modules/",
    "/client/__tests__/setup/setupTests.js"
  ],
  testPathIgnorePatterns: [
    "/node_modules/",
    "/client/__tests__/setup/"
  ],
  transformIgnorePatterns: [
    "/node_modules/"
  ],
  testEnvironment: "jsdom"
};
