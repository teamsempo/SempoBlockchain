import Select from "react-select";
import React from "react";

export const MultipleChoice = (props: any) => {
  const { name, input, options } = props;

  const parsedOptions = options.map((option: string) => ({
    value: option,
    label: option
  }));
  return (
    <Select
      {...input}
      name={name}
      defaultValue={[parsedOptions[0]]}
      options={parsedOptions}
      isMulti={true}
      onChange={value => input.onChange(value)}
      onBlur={() => input.onBlur(input.value)}
    />
  );
};
