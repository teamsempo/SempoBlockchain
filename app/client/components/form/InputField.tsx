import React from "react";
import {Field} from "redux-form";

import FormValidation from "./FormValidation";
import {AdaptedInput} from "./WrappedInput";

//should move checkbox into its own kind? would have diff styling
interface InputFieldJson {
  name: string,
  type?: "text" | "checkbox" | "email" | "password",
  label?: string,
  placeholder?: string,
  isRequired?: boolean,
  isPhoneNumber?: boolean,
  children?: React.ReactNode
}


export default function InputField(props: InputFieldJson) {
  const { name, label, isRequired, isPhoneNumber, placeholder, type, children} = props;

  let validate = [];
  if (isRequired) {
    validate.push(FormValidation.required)
  }
  if (isPhoneNumber) {
    validate.push(FormValidation.phone)
  }

  return <Field
    name={name}
    component={AdaptedInput}
    type={type || "text"}
    placeholder={placeholder}
    validate={validate}
    isRequired={isRequired}
    label={label}
    children={children}
  />
};

