import * as React from "react";

import { Link } from "react-router-dom";

import { Table, Button, Checkbox, Tag } from "antd";

import { ColumnsType } from "antd/es/table";

import { ReduxState } from "../../reducers/rootReducer";
import { connect } from "react-redux";
import { formatMoney, maybe } from "../../utils";
import DateTime from "../dateTime";

interface StateProps {
  transferAccounts: any;
  users: any;
  tokens: any;
}

interface DispatchProps {}

interface OuterProps {
  orderedTransferAccounts: number[];
  users: any;
  actionButtons: ActionButton[];
  noneSelectedbuttons: NoneSelectedButton[];
  onSelectChange?: (
    selectedRowKeys: React.Key[],
    selectedRows: TransferAccount[]
  ) => void;
}

interface ComponentState {
  selectedRowKeys: React.Key[];
}

export interface TransferAccount {
  key: number;
  first_name: string;
  last_name: string;
  created: string;
  balance: number;
  token_symbol: string;
}

export interface ActionButton {
  label: string;
  onClick: (keys: React.Key[]) => void;
  loading?: boolean;
}

export interface NoneSelectedButton {
  label: string;
  onClick: () => void;
  loading?: boolean;
}

type Props = StateProps & DispatchProps & OuterProps;

const columns: ColumnsType<TransferAccount> = [
  {
    title: "Name",
    key: "name",
    ellipsis: true,
    render: (text: any, record: any) => (
      <Link
        to={"/accounts/" + record.key}
        style={{
          textDecoration: "underline",
          color: "#000000a6",
          fontWeight: 400
        }}
      >
        {record.first_name} {record.last_name}
      </Link>
    )
  },
  {
    title: "Role",
    key: "role",
    render: (text: any, record: any) => {
      let vendorTag = record.is_vendor && <Tag color="#e2a963">Vendor</Tag>;
      let beneficiaryTag = record.is_beneficiary && (
        <Tag color="#62afb0">Beneficiary</Tag>
      );

      return (
        <>
          {vendorTag}
          {beneficiaryTag}
        </>
      );
    }
  },
  {
    title: "Created",
    key: "created",
    render: (text: any, record: any) => <DateTime created={record.created} />
  },
  {
    title: "Balance",
    key: "balance",
    render: (text: any, record: any) => {
      const money = formatMoney(
        record.balance / 100,
        undefined,
        undefined,
        undefined,
        record.token_symbol
      );
      return <p style={{ margin: 0 }}>{money}</p>;
    }
  },
  {
    title: "Status",
    key: "status",
    render: (text: any, record: any) =>
      record.is_approved ? (
        <Tag color="#9bdf56">Approved</Tag>
      ) : (
        <Tag color="#ff715b">Not Approved</Tag>
      )
  }
];

const mapStateToProps = (state: ReduxState): StateProps => {
  return {
    tokens: state.tokens,
    transferAccounts: state.transferAccounts,
    users: state.users
  };
};

class TransferAccountList extends React.Component<Props, ComponentState> {
  constructor(props: Props) {
    super(props);

    this.state = {
      selectedRowKeys: [] // Check here to configure the default column
    };
  }

  onSelectChange = (
    selectedRowKeys: React.Key[],
    selectedRows: TransferAccount[]
  ) => {
    this.setState({ selectedRowKeys });

    if (this.props.onSelectChange) {
      // after setting the state
      // transparently pass through the callback to parent, in case it's needed there
      this.props.onSelectChange(selectedRowKeys, selectedRows);
    }
  };

  toggleSelectAll = (keys: React.Key[], data: TransferAccount[]) => {
    this.setState({
      selectedRowKeys: keys.length === data.length ? [] : data.map(r => r.key)
    });
  };

  render() {
    const { selectedRowKeys } = this.state;
    const {
      actionButtons,
      noneSelectedbuttons,
      orderedTransferAccounts,
      transferAccounts,
      users,
      tokens
    } = this.props;

    let data: TransferAccount[] = orderedTransferAccounts
      .filter(
        (accountId: number) => transferAccounts.byId[accountId] != undefined
      )
      .map((accountId: number) => {
        let transferAccount = transferAccounts.byId[accountId];
        let user = users.byId[transferAccount.primary_user_id];
        let token_symbol = maybe(tokens.byId, [
          transferAccount.token,
          "symbol"
        ]);

        return {
          key: accountId,
          first_name: user.first_name,
          last_name: user.last_name,
          is_vendor: user.is_vendor,
          is_beneficiary: user.is_beneficiary,
          created: transferAccount.created,
          balance: transferAccount.balance,
          is_approved: transferAccount.is_approved,
          token_symbol: token_symbol
        };
      });

    console.log("data length is: ", data.length);

    const headerCheckbox = (
      <Checkbox
        checked={selectedRowKeys.length > 0}
        indeterminate={
          selectedRowKeys.length > 0 && selectedRowKeys.length < data.length
        }
        onChange={e => this.toggleSelectAll(selectedRowKeys, data)}
      />
    );

    const rowSelection = {
      onChange: this.onSelectChange,
      selectedRowKeys: selectedRowKeys,
      columnTitle: headerCheckbox
    };

    let actionButtonElems = actionButtons.map((button: ActionButton) => (
      <Button
        key={button.label}
        onClick={() => button.onClick(selectedRowKeys)}
        loading={button.loading || false}
        disabled={selectedRowKeys.length === 0}
        type="default"
        style={{ minWidth: "150px", margin: "10px" }}
      >
        {button.label}
      </Button>
    ));

    let noneSelectedButtonElems = noneSelectedbuttons.map(
      (button: NoneSelectedButton) => (
        <Button
          key={button.label}
          onClick={() => button.onClick()}
          loading={button.loading || false}
          type="default"
          style={{ minWidth: "150px", margin: "10px" }}
        >
          {button.label}
        </Button>
      )
    );

    const hasSelected = selectedRowKeys.length > 0;
    return (
      <div>
        <div style={{ display: "flex", justifyContent: "space-between" }}>
          <div style={{}}>{actionButtonElems}</div>
          <div style={{ display: "flex", alignItems: "center" }}>
            {hasSelected ? (
              <span style={{ marginRight: "10px" }}>
                {" "}
                {`${selectedRowKeys.length} Selected`}{" "}
              </span>
            ) : (
              noneSelectedButtonElems
            )}
          </div>
        </div>
        <Table
          loading={transferAccounts.loadStatus.isRequesting}
          columns={columns}
          dataSource={data}
          rowSelection={rowSelection}
          style={{ marginLeft: "10px", marginRight: "10px" }}
          pagination={{ pageSize: 50 }}
        />
      </div>
    );
  }
}

export default connect(mapStateToProps)(TransferAccountList);
