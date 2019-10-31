import React from "react";

import styles from "./styles.module.css";

const TextInput = ({
  input,
  label,
  type,
  children,
  meta: { touched, error, warning }
}) => (
  <div className={styles.inputBlock}>
    <label className={styles.inputLabel}>{label}:</label>
    <div style={{display: 'flex'}}>
      <input className={styles.input} {...input} type={type} />
      {children}
    </div>
    <div>
      {touched &&
      ((error && <span className={styles.error}>{error}</span>) ||
        (warning && <span>{warning}</span>))}
    </div>
  </div>
);

export default TextInput;
