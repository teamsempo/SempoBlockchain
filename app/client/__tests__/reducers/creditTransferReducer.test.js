import configureMockStore from 'redux-mock-store';
import { connect } from 'react-redux';
import {
  take,
  fork,
  put,
  takeEvery,
  call,
  all,
  cancelled,
  cancel,
  race,
} from 'redux-saga/effects';
import createSagaMiddleware from 'redux-saga';
import fetchMock from 'fetch-mock';
import enzyme from 'enzyme';
import {
  loadCreditTransferList,
  LOAD_CREDIT_TRANSFER_LIST_REQUEST,
  LOAD_CREDIT_TRANSFER_LIST_SUCCESS,
} from '../../reducers/creditTransferReducer';

const sagaMiddleware = createSagaMiddleware();

const middlewares = [sagaMiddleware];
const mockStore = configureMockStore(middlewares);

describe('async actions', () => {
  it('creates a loadCreditTransferList request', () => {
    const filter = null;
    const id = null;

    const expectedActions = [
      { type: LOAD_CREDIT_TRANSFER_LIST_REQUEST },
      {
        type: LOAD_CREDIT_TRANSFER_LIST_SUCCESS,
        body: { transferList: [], transferStats: {} },
      },
    ];
    const store = mockStore({ transferList: [], transferStats: {} });

    const mapDispatchToProps = dispatch => ({
      loadCreditTransferList: (filter, id) =>
        dispatch(loadCreditTransferList(filter, id)),
    });
    connect(mapDispatchToProps);

    return loadCreditTransferList(filter, id).then(() => {
      // try {
      //   const credit_load_result = fetchMock.get('/api/credit_transfer/').then(() => put({type: LOAD_CREDIT_TRANSFER_LIST_SUCCESS, credit_load_result}))
      // } catch (error) {
      //   put({type: LOAD_CREDIT_TRANSFER_LIST_FAILURE, error: error.statusText})
      // }
      expect(store.getActions()).toEqual(expectedActions);
    });
  });
});

describe('actions', () => {
  it('should create an action to add a todo', () => {
    const filter = null;
    const id = null;

    const text = 'Finish docs';
    const expectedAction = {
      type: LOAD_CREDIT_TRANSFER_LIST_REQUEST,
      text,
    };
    expect(loadCreditTransferList(filter, id)).toEqual(expectedAction);
  });
});
