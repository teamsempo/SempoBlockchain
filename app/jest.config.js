// jest.config.js
const { jsWithBabel: tsjPreset } = require("ts-jest/presets");

module.exports = {
  verbose: true,
  roots: ["./client"],
  collectCoverageFrom: [
    //TODO(COV): Get Typescript coverage working for untested files
    "**/*.{js,jsx}",
    "!**/node_modules/**"
  ],
  globals: {
    // this is needed to use our babel.config.js settings
    "ts-jest": {
      babelConfig: require("./babel.config.js")
    }
  },
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
  transformIgnorePatterns: ["/node_modules/"]
};
