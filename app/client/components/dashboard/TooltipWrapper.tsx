import * as React from "react";
import { Tooltip } from "antd";
import { QuestionCircleFilled } from "@ant-design/icons";
import { toTitleCase } from "../../utils";

interface Props {
  label: string;
  prompt: string;
}

export const TooltipWrapper: React.FunctionComponent<Props> = props => {
  return (
    <Tooltip title={props.prompt}>
      <span>
        {toTitleCase(props.label)}
        <QuestionCircleFilled
          style={{ marginLeft: 4, opacity: 0.4 }}
          translate={""}
        />
      </span>
    </Tooltip>
  );
};
