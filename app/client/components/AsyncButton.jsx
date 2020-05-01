import React from "react";
import { StyledButton } from "./styledElements";

export default class AsyncButton extends React.Component {
  render() {
    if (this.props.isLoading) {
      return (
        <StyledButton
          type={this.props.type}
          onClick={() => null}
          theme={this.props.theme}
          style={{
            ...this.props.buttonStyle,
            position: "relative",
            alignItems: "center",
            justifyContent: "center"
          }}
        >
          <div style={{ position: "absolute" }}>
            <div
              style={{ ...this.props.miniSpinnerStyle }}
              className="miniSpinner"
            ></div>
          </div>
          <div style={{ opacity: 0 }}> {this.props.buttonText} </div>
        </StyledButton>
      );
    } else if (this.props.isSuccess) {
      return (
        <StyledButton
          type={this.props.type}
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
        type={this.props.type}
        onClick={this.props.onClick}
        theme={this.props.theme}
        style={{
          ...this.props.buttonStyle,
          position: "relative",
          alignItems: "center",
          justifyContent: "center"
        }}
      >
        {" "}
        {this.props.buttonText}{" "}
      </StyledButton>
    );
  }
}
