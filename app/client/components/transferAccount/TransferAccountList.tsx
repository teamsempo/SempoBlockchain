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

export interface OnSelectChange {
  (
    selectedRowKeys: React.Key[],
    unselectedRowKeys: React.Key[],
    allSelected: boolean
  ): void;
}

interface OuterProps {
  orderedTransferAccounts: number[];
  users: any;
  actionButtons: ActionButton[];
  noneSelectedbuttons: NoneSelectedButton[];
  onSelectChange?: OnSelectChange;
}

interface ComponentState {
  selectedRowKeys: React.Key[];
  unselectedRowKeys: React.Key[];
  allSelected: boolean;
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
  onClick: OnSelectChange;
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
      selectedRowKeys: [],
      unselectedRowKeys: [],
      allSelected: false
    };
  }

  onSelectChange = (
    record: TransferAccount,
    selected: boolean,
    selectedRows: TransferAccount[],
    nativeEvent: Event
  ) => {
    console.log("selected", selected);
    console.log("record", record);

    let selectedRowKeys = selectedRows.map(r => r.key);
    this.setState({ selectedRowKeys });

    let unselectedRowKeys: React.Key[] = [];
    if (this.state.allSelected) {
      // We only define the unselected rows when the "select all" box has been flagged as true (ie a "default selected" state),
      // because unselected rows isn't specific enough when you start from a "default unselected" state
      let selectedSet = new Set(selectedRowKeys);
      unselectedRowKeys = this.props.orderedTransferAccounts.filter(
        id => !selectedSet.has(id)
      );
    }

    this.setState({ selectedRowKeys, unselectedRowKeys });

    if (this.props.onSelectChange) {
      // after setting the state
      // transparently pass through the callback to parent, in case it's needed there
      this.props.onSelectChange(
        selectedRowKeys,
        unselectedRowKeys,
        this.state.allSelected
      );
    }
  };

  toggleSelectAll = (keys: React.Key[], data: TransferAccount[]) => {
    if (keys.length === data.length) {
      this.setState({
        selectedRowKeys: [],
        unselectedRowKeys: [],
        allSelected: false
      });
    } else {
      this.setState({
        selectedRowKeys: data.map(r => r.key),
        unselectedRowKeys: [],
        allSelected: true
      });
    }
  };

  render() {
    const { selectedRowKeys, unselectedRowKeys, allSelected } = this.state;
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
      onSelect: this.onSelectChange,
      selectedRowKeys: selectedRowKeys,
      columnTitle: headerCheckbox
    };

    let actionButtonElems = actionButtons.map((button: ActionButton) => (
      <Button
        key={button.label}
        onClick={() =>
          button.onClick(selectedRowKeys, unselectedRowKeys, allSelected)
        }
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
                {`${
                  allSelected ? "All" : selectedRowKeys.length
                } Selected`}{" "}
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
          pagination={{ pageSize: 10 }}
        />
      </div>
    );
  }
}

export default connect(mapStateToProps)(TransferAccountList);
