import "isomorphic-fetch";
import { configure } from "enzyme";
import Adapter from "enzyme-adapter-react-16";

configure({ adapter: new Adapter() });

import "../../__mocks__/local-storage-mock.js";
import mockStore from "../../__mocks__/redux-mock-store.js";

jest.mock("../../createStore.js", () => mockStore);
