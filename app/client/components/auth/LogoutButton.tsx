import React from "react";
import { useDispatch } from "react-redux";
import { Button } from "antd";
import { LoginAction } from "../../reducers/auth/actions";

export const LogoutButton = () => {
  const dispatch: any = useDispatch();

  let logout = () => {
    dispatch(LoginAction.apiLogout());
  };
  return (
    <Button type="primary" onClick={logout}>
      Logout
    </Button>
  );
};
