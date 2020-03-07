export interface Action<T extends string> {
  type: T;
}

export interface ActionWithPayload<T extends string, P> extends Action<T> {
  payload: P;
}

export interface ActionWithError<T extends string, P> extends Action<T> {
  error: P;
}

export function createAction<T extends string>(type: T): Action<T>;
export function createAction<T extends string, P extends string>(
  type: T,
  error: P
): ActionWithError<T, P>;
export function createAction<T extends string, P>(
  type: T,
  payload: P
): ActionWithPayload<T, P>;
export function createAction<T extends string, P, V>(type: T, data?: P) {
  if (typeof data === "string") {
    return { type, error: data };
  } else if (typeof data != "undefined") {
    return { type, payload: data };
  } else {
    return { type };
  }
}

type FunctionType = (...args: any[]) => any;
type ActionCreatorsMapObject = { [actionCreator: string]: FunctionType };

export type ActionsUnion<T extends ActionCreatorsMapObject> = ReturnType<
  T[keyof T]
>;

// reference: https://medium.com/@martin_hotell/improved-redux-type-safety-with-typescript-2-8-2c11a8062575
