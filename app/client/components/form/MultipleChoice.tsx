import React from "react";
import { Select } from "antd";

const { Option } = Select;

export const MultipleChoice = (props: any) => {
  const { name, input, options, style } = props;

  const parsedOptions = options.map((option: string) => (
    <Option key={option} value={option}>
      {option}
    </Option>
  ));

  return (
    <Select
      mode="multiple"
      allowClear
      style={style}
      placeholder="Please select"
      onChange={value => input.onChange(value)}
      onBlur={() => input.onBlur(input.value)}
      value={input.value}
    >
      {parsedOptions}
    </Select>
  );
};
