import {
  UserListActionTypes,
  CreateUserActionTypes,
  DeleteUserActionTypes,
  EditUserActionTypes,
  LoadUserActionTypes,
  ResetPinActionTypes,
  User,
  LoadUserRequestPayload,
  CreateUserPayload,
  ResetPinPayload,
  DeleteUserPayload,
  EditUserPayload,
  CreateUserSuccessPayload
} from "./types";
import { createAction, ActionsUnion } from "../../reduxUtils";

export const UserListAction = {
  updateUserList: (users: User[]) =>
    createAction(UserListActionTypes.UPDATE_USER_LIST, users),
  deepUpdateUserList: (users: User[]) =>
    createAction(UserListActionTypes.DEEP_UPDATE_USER_LIST, users)
};
export type UserListAction = ActionsUnion<typeof UserListAction>;

export const LoadUserAction = {
  loadUserRequest: (payload: LoadUserRequestPayload) =>
    createAction(LoadUserActionTypes.LOAD_USER_REQUEST, payload),
  loadUserSuccess: () => createAction(LoadUserActionTypes.LOAD_USER_SUCCESS),
  loadUserFailure: (error: string) =>
    createAction(LoadUserActionTypes.LOAD_USER_FAILURE, error)
};
export type LoadUserAction = ActionsUnion<typeof LoadUserAction>;

export const CreateUserAction = {
  createUserRequest: (payload: CreateUserPayload) =>
    createAction(CreateUserActionTypes.CREATE_USER_REQUEST, payload),
  createUserSuccess: (payload: CreateUserSuccessPayload) =>
    createAction(CreateUserActionTypes.CREATE_USER_SUCCESS, payload),
  createUserFailure: (error: string) =>
    createAction(CreateUserActionTypes.CREATE_USER_FAILURE, error),
  resetCreateUser: () => createAction(CreateUserActionTypes.RESET_CREATE_USER)
};
export type CreateUserAction = ActionsUnion<typeof CreateUserAction>;

export const EditUserAction = {
  editUserRequest: (payload: EditUserPayload) =>
    createAction(EditUserActionTypes.EDIT_USER_REQUEST, payload),
  editUserSuccess: () => createAction(EditUserActionTypes.EDIT_USER_SUCCESS),
  editUserFailure: (error: string) =>
    createAction(EditUserActionTypes.EDIT_USER_FAILURE, error)
};
export type EditUserAction = ActionsUnion<typeof EditUserAction>;

export const DeleteUserAction = {
  deleteUserRequest: (payload: DeleteUserPayload) =>
    createAction(DeleteUserActionTypes.DELETE_USER_REQUEST, payload),
  deleteUserSuccess: () =>
    createAction(DeleteUserActionTypes.DELETE_USER_SUCCESS),
  deleteUserFailure: (error: string) =>
    createAction(DeleteUserActionTypes.DELETE_USER_FAILURE, error)
};
export type DeleteUserAction = ActionsUnion<typeof DeleteUserAction>;

export const ResetPinAction = {
  resetPinRequest: (payload: ResetPinPayload) =>
    createAction(ResetPinActionTypes.RESET_PIN_REQUEST, payload),
  resetPinSuccess: () => createAction(ResetPinActionTypes.RESET_PIN_SUCCESS),
  resetPinFailure: (error: string) =>
    createAction(ResetPinActionTypes.RESET_PIN_FAILURE, error)
};
export type ResetPinAction = ActionsUnion<typeof ResetPinAction>;
