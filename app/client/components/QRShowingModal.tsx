import React, { Suspense, lazy, useState } from "react";
import { Modal } from "antd";

const QRCode = lazy(() => import("qrcode.react"));

type QrProps = {
  data: string;
};

type QrState = {
  visible: boolean;
};

export default class QRShowingModal extends React.Component<QrProps, QrState> {
  state = {
    visible: false
  };

  showModal = () => {
    this.setState({
      visible: true
    });
  };

  handleCancel = () => {
    this.setState({ visible: false });
  };

  render() {
    const { visible } = this.state;
    return (
      <>
        <div
          style={{
            margin: "0.2em",
            width: "1.4em",
            height: "1.4em",
            cursor: "pointer"
          }}
          onClick={() => this.showModal()}
        >
          <img style={{ width: "100%" }} src={"/static/media/qrCodeIcon.svg"} />
        </div>

        <Modal
          visible={visible}
          title="Scan this QR code to quickly log in to an integration"
          onCancel={this.handleCancel}
          footer={null}
          bodyStyle={{ display: "flex", justifyContent: "center" }}
        >
          <Suspense fallback={<div>Loading QR Code...</div>}>
            <QRCode
              style={{ margin: "1em" }}
              size={256}
              value={this.props.data}
            />
          </Suspense>
        </Modal>
      </>
    );
  }
}
