import * as React from "react";

import * as styles from "./styles.module.css";

import { AdaptedPhoneInput } from "./Phone";
import { MultipleChoice } from "./MultipleChoice";

export const WrappedInput = (field: React.ReactNode, props: any) => {
  const { label, isRequired, meta, children } = props;
  const { touched, error, warning } = meta;

  return (
    <div className={styles.inputBlock}>
      <label className={styles.inputLabel}>
        {label}:{" "}
        {isRequired ? <span className={styles.required}>*</span> : null}
      </label>
      <div style={{ display: "flex" }}>
        {field}
        {children}
      </div>
      <div>
        {touched &&
          ((error && <span className={styles.error}>{error}</span>) ||
            (warning && <span>{warning}</span>))}
      </div>
    </div>
  );
};

export const AdaptedInput = (props: any) => {
  const {
    name,
    type,
    input,
    placeholder,
    disabled,
    isPhoneNumber,
    isMultipleChoice,
    style
  } = props;

  const field = isMultipleChoice ? (
    <MultipleChoice {...props} />
  ) : isPhoneNumber ? (
    <AdaptedPhoneInput {...props} />
  ) : (
    <input
      className={styles.input}
      placeholder={placeholder}
      name={name}
      disabled={disabled}
      type={type}
      style={style}
      {...input}
    />
  );

  return WrappedInput(field, props);
};
