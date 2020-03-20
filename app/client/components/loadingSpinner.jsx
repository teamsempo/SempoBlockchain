import React from 'react';

export default class LoadingSpinner extends React.Component {
  render() {
    return (
      <div style={{ ...this.props.spinnerStyle }} className="mainSpinner" />
    );
  }
}
