import React from "react";
import { StyledButton } from "./styledElements";

interface Props {
  isLoading?: boolean,
  type?: "button" | "submit" | "reset" | undefined,
  theme?: string,
  buttonStyle?: React.CSSProperties,
  miniSpinnerStyle?: React.CSSProperties,
  buttonText?: string,
  isSuccess?: boolean,
  onClick?: () => any,

}

export function AsyncButton(props: Props) {
  const {isLoading, type, theme, buttonStyle, miniSpinnerStyle, buttonText, isSuccess, onClick} = props
  if (isLoading) {
    return (
      <StyledButton
        type={type}
        onClick={() => null}
        theme={theme}
        style={{
          ...buttonStyle,
          position: "relative",
          alignItems: "center",
          justifyContent: "center"
        }}
      >
        <div style={{ position: "absolute" }}>
          <div
            style={{ ...miniSpinnerStyle }}
            className="miniSpinner"
          ></div>
        </div>
        <div style={{ opacity: 0 }}> {buttonText} </div>
      </StyledButton>
    );
  } else if (isSuccess) {
    return (
      <StyledButton
        type={type}
        onClick={() => null}
        style={{
          display: "flex",
          position: "relative",
          alignItems: "center",
          justifyContent: "center"
        }}
      >
        {" "}
        Success{" "}
      </StyledButton>
    );
  }
  return (
    <StyledButton
      type={type}
      onClick={onClick}
      theme={theme}
      style={{
        ...buttonStyle,
        position: "relative",
        alignItems: "center",
        justifyContent: "center"
      }}
    >
      {" "}
      {buttonText}{" "}
    </StyledButton>
  );
}

