import React from "react";
import { StyledButton } from "./styledElements";
import LoadingSpinner from "./loadingSpinner";

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
          label={this.props.label}
        >
          <div style={{ position: "absolute" }}>
            <LoadingSpinner style={{ color: "white" }} />
          </div>
          <div style={{ opacity: 0 }}>
            <span>{this.props.buttonText}</span>
          </div>
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
          label={this.props.label}
        >
          <span> Success </span>
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
        label={this.props.label}
      >
        <span> {this.props.buttonText} </span>
      </StyledButton>
    );
  }
}
