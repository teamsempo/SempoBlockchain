import * as Sentry from "@sentry/browser";
import * as React from "react";

import PhoneInput from "react-phone-input-2";
import "react-phone-input-2/lib/plain.css";
import store from "../../createStore.js";

export const AdaptedPhoneInput = (props: any) => {
  const { name, input, placeholder, disabled, isPhoneNumber } = props;

  let countryCode;
  let orgId;

  if (isPhoneNumber) {
    try {
      orgId = store && store.getState().login.organisationId;
      countryCode =
        orgId && store.getState().organisations.byId[orgId].country_code;
    } catch (e) {
      countryCode = undefined;
      Sentry.captureException(e);
    }
  }

  return (
    <PhoneInput
      country={countryCode && countryCode.toLowerCase()}
      placeholder={placeholder}
      name={name}
      disabled={disabled}
      {...input}
      {...props}
      inputClass={"ant-input"}
      containerClass={"ant-form-item-control-input-content"}
      dropdownClass={"ant-dropdown-menu"}
    />
  );
};
