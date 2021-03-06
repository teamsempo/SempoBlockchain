import React from "react";
import { Button } from "antd";
import { UsergroupAddOutlined } from "@ant-design/icons";
import ImportModal from "./importModal.jsx";

export default class ImportButton extends React.Component {
  constructor() {
    super();
    this.state = {
      modalVisible: false
    };
  }

  toggleModal() {
    this.setState({ modalVisible: !this.state.modalVisible });
  }

  render() {
    const { type, size, showIcon } = this.props;
    const { modalVisible } = this.state;

    return (
      <div>
        <ImportModal
          isModalVisible={modalVisible}
          handleOk={() => this.toggleModal()}
          handleCancel={() => this.toggleModal()}
        />

        <Button
          key={"Add Account"}
          onClick={() => this.toggleModal()}
          type={type || "default"}
          style={{ minWidth: "150px", margin: "10px" }}
          size={size || "middle"}
          icon={showIcon ? <UsergroupAddOutlined /> : undefined}
        >
          Add Account
        </Button>
      </div>
    );
  }
}
