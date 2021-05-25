import React from "react";
import { useSelector, useDispatch } from "react-redux";
import { Modal, Tooltip, List } from "antd";

import { DollarCircleOutlined } from "@ant-design/icons";
import { grey } from "@ant-design/colors";
import { Organisation } from "../../reducers/organisation/types";
import { ReduxState } from "../../reducers/rootReducer";
import { LoginAction } from "../../reducers/auth/actions";
import { formatMoney } from "../../utils";

interface OuterProps {
  isModalVisible: boolean;
  handleOk: any;
  handleCancel: any;
}

export const WalletListModal = (props: OuterProps) => {
  const dispatch: any = useDispatch();
  const organisations: Organisation[] = useSelector((state: ReduxState) =>
    Object.keys(state.organisations.byId).map(
      id => state.organisations.byId[Number(id)]
    )
  );

  let selectOrg = (organisationIds: number[]) => {
    dispatch(
      LoginAction.updateActiveOrgRequest({
        organisationIds,
        isManageWallet: true
      })
    );
  };

  return (
    <span>
      <Tooltip title={"Manage Project Master Wallet's"} placement="rightTop">
        <a
          onClick={props.handleOk}
          style={{ padding: "0 0 0 5px", color: grey[4] }}
        >
          <DollarCircleOutlined translate={""} />
        </a>
      </Tooltip>
      <Modal
        zIndex={1051}
        title="Project Wallet's"
        visible={props.isModalVisible}
        onOk={props.handleOk}
        onCancel={props.handleCancel}
      >
        <List
          dataSource={organisations}
          renderItem={org => (
            <List.Item
              actions={[
                <a key="list-loadmore-edit" onClick={() => selectOrg([org.id])}>
                  Manage
                </a>
              ]}
            >
              <List.Item.Meta
                title={org.name}
                description={`Balance: ${formatMoney(
                  org.master_wallet_balance
                )}`}
              />
            </List.Item>
          )}
        />
      </Modal>
    </span>
  );
};
