import React from "react";
import { Modal, List } from "antd";
import {
  FileAddOutlined,
  UserAddOutlined,
  NodeIndexOutlined
} from "@ant-design/icons";
import { NavLink } from "react-router-dom";

const fontSize = 20;
const style = { fontSize: fontSize };
const data = [
  {
    title: "Add Individual Account",
    to: "/create",
    icon: <UserAddOutlined style={style} />
  },
  {
    title: "Upload XLSX/CSV",
    to: "/upload",
    icon: <FileAddOutlined style={style} />
  },
  {
    title: "Connect Kobo Toolbox or Commcare",
    to: "/settings",
    icon: <NodeIndexOutlined style={style} />
  }
];

const ImportModal = props => {
  return (
    <div>
      <Modal
        title="Import Data"
        visible={props.isModalVisible}
        onOk={props.handleOk}
        onCancel={props.handleCancel}
      >
        <List
          size="large"
          itemLayout="horizontal"
          dataSource={data}
          renderItem={item => (
            <List.Item>
              <List.Item.Meta
                avatar={item.icon}
                title={<NavLink to={item.to}>{item.title}</NavLink>}
              />
            </List.Item>
          )}
        />
      </Modal>
    </div>
  );
};
export default ImportModal;
