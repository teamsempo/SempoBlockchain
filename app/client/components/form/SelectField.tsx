import React from 'react'
import {Field} from 'redux-form'

import {WrappedInput} from './WrappedInput'
import styles from "./styles.module.css";
import FormValidation from "./FormValidation";

interface SelectFieldJson {
  name: string,
  options: ({name: string, value: string} | string)[],
  label?: string,
  isRequired?: boolean
}

const SelectInput = (props: SelectFieldJson & {input: any}) => {
  const {name, input, options} = props;

  const field = <select className={styles.input} value={input.value} name={name} {...input}>
    {
      options.map((option) => {
        if (typeof option === "string") {
          const value = option.toLowerCase();
          return <option value={value} key={value}>{option}</option>
        } else {
          const {name, value} = option;
          return <option value={value} key={value}>{name}</option>
        }
      })
    }
  </select>;

  return WrappedInput(field, props)
};

export default function SelectField(props: SelectFieldJson) {
  const { label, name, options, isRequired} = props;

  let validate = [];
  if (isRequired) {
    validate.push(FormValidation.required)
  }

  return <Field
    name={name}
    component={SelectInput}
    label={label}
    options={options}
    validate={validate}
    isRequired={isRequired}
  />
}