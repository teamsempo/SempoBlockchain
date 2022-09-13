import {
  createActionTypes,
  loadActionTypes,
  modifyActionTypes,
} from "./actions";
import { sagaFactory } from "./sagas";
import { combineReducers, ReducersMapObject } from "redux";
import {
  byIdReducerFactory,
  idListReducerFactory,
  lifecycleReducerFactory,
  paginationReducerFactory,
  asyncIdReducerFactory,
} from "./reducers";
import {
  EndpointedRegistration,
  RegistrationMapping,
  Registration,
  EndpointedRegistrationMapping,
} from "./types";

export { apiActions } from "./actions";
export {
  Registration,
  LoadRequestAction,
  CreateRequestAction,
  ModifyRequestAction,
} from "./types";
export { Body } from "../api/client/types";

function hasEndpoint(
  reg: Registration | EndpointedRegistration
): reg is EndpointedRegistration {
  return (reg as EndpointedRegistration).endpoint !== undefined;
}

/**
 * Creates a set of reducers for each object defined in the registration mapping.
 * By default creates a map of each instance of an object indexed by the instance's ID. This map is deep-merged
 * whenever a REST API call triggered by _any_ of the registered objects results in updated data for that object
 * Additionally if an API endpoint is defined, will also create lifecycle reducers corresponding
 * to loading, creating and modifying an object, as well as an ordered ID list that is updated when new data is loaded
 *
 * @param {RegistrationMapping} registrations - a mapping of each object to be registered
 * @returns An array of reducers
 */
export const createReducers = <R extends RegistrationMapping>(
  registrations: R
): ReducersMapObject<R> => {
  const base: ReducersMapObject = {};

  Object.keys(registrations).map((key) => {
    let reg = { ...registrations[key], name: key };

    let reducers = {
      byId: byIdReducerFactory(reg),
    };

    if (hasEndpoint(reg)) {
      reducers = {
        ...reducers,
        ...{
          loadStatus: lifecycleReducerFactory(loadActionTypes, reg),
          createStatus: lifecycleReducerFactory(createActionTypes, reg),
          modifyStatus: lifecycleReducerFactory(modifyActionTypes, reg),
          idList: idListReducerFactory(reg),
          pagination: paginationReducerFactory(reg),
          asyncId: asyncIdReducerFactory(reg),
        },
      };
    }

    base[reg.name] = combineReducers(reducers);
  });

  return base;
};

/**
 * Creates REST API sagas for loading, creating and modifying objects. An object must have an endpoint defined for
 * a saga to be created
 * @param {RegistrationMapping} registrations - a mapping of each object to be registered
 * @returns {any[]}
 */
export const createSagas = (registrations: RegistrationMapping) => {
  let sagaList: any[] = [];

  let endpointedRegistrations: EndpointedRegistrationMapping = {};

  //First ensure all registrations have a name and filter out all non-endpointed registrations
  //Done in that order rather than using .filter for type safety
  Object.keys(registrations).map((key) => {
    let reg = { ...registrations[key], name: key };
    if (hasEndpoint(reg)) {
      endpointedRegistrations[key] = reg;
    }
  });

  Object.keys(endpointedRegistrations).map((key) => {
    sagaList.push(
      sagaFactory(endpointedRegistrations[key], endpointedRegistrations)()
    );
  });

  return sagaList;
};

/**
 * ~~~~~For example~~~~~
 *
 *
 *  interface CreateUserBody {
 *   first_name: string;
 *   last_name: string;
 *   public_serial_number: string;
 *   //  And so on
 * }
 *
 * interface ModifyUserBody {
 *   //Defaults to the same as create body, but can be different
 *   first_name: string;
 *   last_name: string;
 *   some_other_thing: boolean;
 *   //  And so on
 * }
 *
 * interface SempoObjects extends RegistrationMapping {
 *   UserExample: Registration<CreateUserBody, ModifyUserBody>;
 * }
 *
 * export const sempoObjects: SempoObjects = {
 *   UserExample: {
 *     name: "UserExample",
 *     endpoint: "user",
 *     schema: userSchema
 *   }
 *
 * let baseReducers = createReducers(sempoObjects);
 * let sagalist = createSagas(sempoObjects);
 *
 * const appReducer = combineReducers({
 *  ...baseReducers
 * });
 *
 * export default function* rootSaga() {
 *    yield all([
 *      generatedSagas()
 *    ]);
 * }
 *
 * Then for dispatch in component:
 * const mapDispatchToProps = (dispatch: any): DispatchProps => {
 *   return {
 *     loadUsers: () => dispatch(apiActions.load(sempoObjects.UserExample))
 *   }
 * }
 */
