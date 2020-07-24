export interface Action<T extends string> {
  type: T;
}

export interface NamedAction<T extends string> extends Action<T>{
  name: string;
}

export interface ActionWithPayload<T extends string, P> extends Action<T> {
  payload: P;
}

export interface ActionWithError<T extends string, P> extends Action<T> {
  error: P;
}

export interface ActionWithPayload<T extends string, P> extends Action<T> {
  payload: P;
}

export interface NamedActionWithPayload<T extends string, P> extends NamedAction<T> {
  payload: P;
}

export interface NamedActionWithError<T extends string, P> extends NamedAction<T> {
  error: P;
}

export interface NamedActionWithPayload<T extends string, P> extends NamedAction<T> {
  payload: P;
}

export function createAction<T extends string>(
  type: T
): Action<T>;
export function createAction<T extends string, P extends string>(
  type: T,
  error: P
): ActionWithError<T, P>;
export function createAction<T extends string, P>(
  type: T,
  payload: P
): ActionWithPayload<T, P>;
export function createAction<T extends string, P>(type: T, data?: P) {
  if (typeof data === "string") {
    return { type, error: data };
  } else if (typeof data != "undefined") {
    return { type, payload: data };
  } else {
    return { type };
  }
}

export function createNamedAction<T extends string>(
  type: T,
  name: string
): NamedAction<T>;
export function createNamedAction<T extends string, P extends string>(
  type: T,
  name: string,
  error: P,
):NamedActionWithError<T, P>;
export function createNamedAction<T extends string, P>(
  type: T,
  name: string,
  payload: P
): NamedActionWithPayload<T, P>;
export function createNamedAction<T extends string, P>(type: T, name: string, data?: P) {
  if (typeof data === "string") {
    return { type, name, error: data };
  } else if (typeof data != "undefined") {
    return { type, name, payload: data };
  } else {
    return { type, name };
  }
}



// export function createAction<T extends string, P extends string>(
//   type: T,
//   error: P
// ): ActionWithError<T, P>;
// export function createAction<T extends string, P>(
//   type: T,
//   payload: P
// ): ActionWithPayload<T, P>;
// export function createAction<T extends string, P>(type: T, data?: P) {
//   if (typeof data === "string") {
//     return { type, error: data };
//   } else if (typeof data != "undefined") {
//     return { type, payload: data };
//   } else {
//     return { type };
//   }
// }
//

type FunctionType = (...args: any[]) => any;
type ActionCreatorsMapObject = { [actionCreator: string]: FunctionType };

export type ActionsUnion<T extends ActionCreatorsMapObject> = ReturnType<
  T[keyof T]
>;
