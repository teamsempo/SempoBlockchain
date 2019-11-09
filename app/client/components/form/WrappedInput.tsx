import React from 'react'

import styles from './styles.module.css'

export const WrappedInput = (field: React.ReactNode, props: any) => {
  const {label, isRequired, meta, children} = props;
  const { touched, error, warning } = meta;

  return <div className={styles.inputBlock}>
    <label className={styles.inputLabel}>{label}: {isRequired ? <span className={styles.required}>*</span> : null}</label>
    <div style={{display: 'flex'}}>
      {field}
      {children}
    </div>
    <div>
      {touched &&
      ((error && <span className={styles.error}>{error}</span>) ||
        (warning && <span>{warning}</span>))}
    </div>
  </div>
};

export const AdaptedInput = (props: any) => {
  const {name, type, input, placeholder} = props;
  const field = <input className={styles.input} placeholder={placeholder} name={name} type={type} {...input} />;

  return WrappedInput(field, props)
};