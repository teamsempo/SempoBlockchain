import React from "react";

interface Props {
  spinnerStyle?: React.CSSProperties
}
export default function LoadingSpinner(props: Props) {
  const {spinnerStyle} = props
  return (
    <div style={{ ...spinnerStyle }} className="mainSpinner"></div>
  );
}
