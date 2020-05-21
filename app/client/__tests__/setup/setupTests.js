import { configure } from "enzyme";
import Adapter from "enzyme-adapter-react-16";

configure({ adapter: new Adapter() });

// adds the 'fetchMock' global variable and rewires 'fetch' global to call 'fetchMock' instead of the real implementation
require("jest-fetch-mock").enableMocks();

import "../../__mocks__/local-storage-mock.js";
import mockStore from "../../__mocks__/redux-mock-store.js";

jest.mock("../../createStore.js", () => mockStore);
