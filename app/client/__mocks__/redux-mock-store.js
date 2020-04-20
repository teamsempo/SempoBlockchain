import configureMockStore from "redux-mock-store";

const middlewares = [];
const mockStore = configureMockStore(middlewares);

// Initialize mockstore with empty state
const initialState = { login: { webApiVersion: 1 } };
const store = mockStore(initialState);

export default store;
