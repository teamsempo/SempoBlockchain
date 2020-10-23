import * as React from "react";
import { Field } from "redux-form";

import FormValidation from "./FormValidation";
import { AdaptedInput } from "./WrappedInput";

//should move checkbox into its own kind? would have diff styling
interface InputFieldJson {
  name: string;
  type?: "text" | "checkbox" | "email" | "password";
  disabled?: boolean;
  label?: string;
  placeholder?: string;
  isRequired?: boolean;
  isPhoneNumber?: boolean;
  isMultipleChoice?: boolean;
  options?: string[];
  isNotOther?: boolean;
  isNumber?: boolean;
  children?: React.ReactNode;
  style?: any;
  defaultValue?: string[];
}

export default function InputField(props: InputFieldJson) {
  const {
    name,
    label,
    isRequired,
    isPhoneNumber,
    isMultipleChoice,
    options,
    isNotOther,
    isNumber,
    placeholder,
    type,
    disabled,
    children,
    style,
    defaultValue
  } = props;

  let validate = [];
  if (isRequired) {
    validate.push(FormValidation.required);
  }
  if (isPhoneNumber) {
    validate.push(FormValidation.phone);
  }
  if (isNotOther) {
    validate.push(FormValidation.notOther);
  }
  if (isNumber) {
    validate.push(FormValidation.isNumber);
  }

  return (
    <Field
      name={name}
      component={AdaptedInput}
      options={options}
      type={type || "text"}
      placeholder={placeholder}
      validate={validate}
      isRequired={isRequired}
      isMultipleChoice={isMultipleChoice}
      label={label}
      disabled={disabled}
      children={children}
      isPhoneNumber={isPhoneNumber}
      style={style}
      defaultValue={defaultValue}
    />
  );
}
