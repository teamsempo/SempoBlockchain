// jest.config.js
const { jsWithBabel: tsjPreset } = require("ts-jest/presets");

module.exports = {
  verbose: true,
  roots: ["<rootDir>/client"],
  collectCoverageFrom: ["**/*.{js,jsx,ts,tsx}", "!**/node_modules/**"],
  globals: {
    // this is needed to use our babel.config.js settings
    "ts-jest": {
      babelConfig: require("./babel.config.js"),
      diagnostics: {
        warnOnly: true
      }
    }
  },
  transform: {
    ...tsjPreset.transform
  },
  moduleNameMapper: {
    "\\.(jpg|jpeg|png|gif|eot|otf|webp|svg|ttf|woff|woff2|mp4|webm|wav|mp3|m4a|aac|oga)$":
      "<rootDir>/tests/client/__mocks__/fileMock.js",
    "\\.(css|less)$": "<rootDir>/client/__mocks__/styleMock.js"
  },
  snapshotSerializers: ["enzyme-to-json/serializer"],
  setupFilesAfterEnv: ["./client/__tests__/setup/setupTests.js"],
  coveragePathIgnorePatterns: [
    "/node_modules/",
    "/client/__tests__/setup/setupTests.js"
  ],
  testPathIgnorePatterns: ["/node_modules/", "/client/__tests__/setup/"],
  transformIgnorePatterns: ["/node_modules/"],
  moduleFileExtensions: ["ts", "tsx", "js", "jsx", "json", "node"]
};
