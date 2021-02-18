import {
  createActionTypes,
  loadActionTypes,
  modifyActionTypes
} from "./actions";
import { sagaFactory } from "./sagas";
import { combineReducers, ReducersMapObject } from "redux";
import {
  byIdReducerFactory,
  IdListReducerFactory,
  lifecycleReducerFactory
} from "./reducers";
import {
  EndpointedRegistration,
  RegistrationMapping,
  Registration,
  EndpointedRegistrationMapping
} from "./types";

export { apiActions } from "./actions";
export {
  Registration,
  LoadRequestAction,
  CreateRequestAction,
  ModifyRequestAction
} from "./types";
export { Body } from "../api/client/types";

function hasEndpoint(
  reg: Registration | EndpointedRegistration
): reg is EndpointedRegistration {
  return (reg as EndpointedRegistration).endpoint !== undefined;
}

export const createReducers = <R extends RegistrationMapping>(
  registrations: R
): ReducersMapObject<R> => {
  const base: ReducersMapObject = {};

  Object.keys(registrations).map(key => {
    let reg = { ...registrations[key], name: key };

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

  let endpointedRegistrations: EndpointedRegistrationMapping = {};

  //First ensure all registrations have a name and filter out all non-endpointed registrations
  //Done in that order rather than using .filter for type safety
  Object.keys(registrations).map(key => {
    let reg = { ...registrations[key], name: key };
    if (hasEndpoint(reg)) {
      endpointedRegistrations[key] = reg;
    }
  });

  Object.keys(endpointedRegistrations).map(key => {
    sagaList.push(
      sagaFactory(endpointedRegistrations[key], endpointedRegistrations)()
    );
  });

  return sagaList;
};
