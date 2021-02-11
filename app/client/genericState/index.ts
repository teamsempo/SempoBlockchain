import {
  createActionTypes,
  loadActionTypes,
  modifyActionTypes
} from "./actions";
import { sagaFactory } from "./sagas";
import { combineReducers } from "redux";
import {
  byIdReducerFactory,
  IdListReducerFactory,
  lifecycleReducerFactory
} from "./reducers";
import {
  BaseReducerMapping,
  HasEndpointRegistration,
  RegistrationMapping,
  Registration
} from "./types";

export { actionFactory } from "./actions";

function hasEndpoint(
  reg: Registration | HasEndpointRegistration
): reg is HasEndpointRegistration {
  return (reg as HasEndpointRegistration).endpoint !== undefined;
}

export const createReducers = (
  registrations: RegistrationMapping
): BaseReducerMapping => {
  const base: BaseReducerMapping = {};

  Object.keys(registrations).map(key => {
    let reg = registrations[key];

    let reducers = {
      byId: byIdReducerFactory(reg),
      IdList: IdListReducerFactory(reg)
    };

    if (hasEndpoint(reg)) {
      reducers = {
        ...reducers,
        ...{
          loadStatus: lifecycleReducerFactory(loadActionTypes, reg),
          createStatus: lifecycleReducerFactory(createActionTypes, reg),
          modifyStatus: lifecycleReducerFactory(modifyActionTypes, reg)
        }
      };
    }

    base[reg.name] = combineReducers(reducers);
  });

  return base;
};

export const createSagas = (registrations: RegistrationMapping) => {
  let sagaList: any[] = [];

  Object.keys(registrations).map(key => {
    let reg = registrations[key];
    if (hasEndpoint(reg)) {
      sagaList.push(sagaFactory(reg, registrations)());
    }
  });

  return sagaList;
};
