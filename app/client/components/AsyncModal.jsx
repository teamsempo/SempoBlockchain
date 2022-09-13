import React, { useState } from "react";
import { connect } from "react-redux";
import { LoadAsyncAction, AsyncAction } from "../reducers/async/actions";
import { Modal, Progress } from "antd";

const mapStateToProps = (state) => {
  return {
    async: state.async,
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    loadAsync: (path) => dispatch(LoadAsyncAction.loadAsyncRequest({ path })),
    clearAsync: () => dispatch(AsyncAction.clearAsync()),
  };
};

class AsyncModal extends React.Component {
  componentDidMount() {
    // Loads status from loadAsync the first time, then uses a timer to get it
    // every second from then on!
    this.timerID = setInterval(() => this.refresh(), 1000);
  }

  componentWillUnmount() {
    clearInterval(this.timerID);
  }

  refresh() {
    if (this.props.async.asyncState.percent_complete == 100) {
      clearInterval(this.timerID);
      // Flushes async data from previous task
      this.props.clearAsync();
      this.props.onComplete();
      return;
    }
    if (this.props.asyncId) {
      this.props.loadAsync(this.props.asyncId);
    }
  }

  render() {
    const percentComplete = this.props.async.asyncState.percent_complete;
    const message = this.props.async.asyncState.message;
    return (
      <Modal
        title={this.props.title}
        visible={this.props.isModalVisible && percentComplete != 100}
        footer={null}
        onCancel={this.onCancel}
        closable={false}
        centered={true}
        width={200}
        bodyStyle={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexDirection: "column",
        }}
      >
        <Progress alignItems="center" type="circle" percent={percentComplete} />
        <br />
        <h3 alignItems="center">{message}</h3>
      </Modal>
    );
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(AsyncModal);
