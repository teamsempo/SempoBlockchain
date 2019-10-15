jest.unmock('redux');
jest.unmock('redux-saga');
jest.unmock('redux-mock-store');
jest.unmock('../../sagas/rootSaga');
jest.unmock('../../reducers/rootReducer');

import React from 'react'
import { shallow,render,mount,configure } from 'enzyme'
import Adapter from 'enzyme-adapter-react-16';
import configureMockStore from 'redux-mock-store'
import createSagaMiddleware from 'redux-saga'
import * as router from 'react-router'

import rootReducer from '../../reducers/rootReducer';
import rootsaga from '../../sagas/rootSaga'

import onBoardingPage from '../../components/pages/authPage.jsx'
import App from '../../app.jsx'

const sagaMiddleware = createSagaMiddleware();
const mockStore = configureMockStore([sagaMiddleware]);

configure({ adapter: new Adapter() });

describe('Main App Tests', () => {
    test('render app', () => {
        router.browserHistory = { push: () => {} };
        const store = mockStore(rootReducer);
        sagaMiddleware.run(rootsaga);
        const app = mount(<App store={store} />);
        expect(app.exists()).toBe(true);
    });
});