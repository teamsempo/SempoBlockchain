import * as React from "react";

import { Table, Button, Checkbox } from "antd";

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

interface ActionButton {
  label: string;
  onClick: (keys: React.Key[]) => void;
  loading?: boolean;
}

interface NoneSelectedButton {
  label: string;
  onClick: () => void;
  loading?: boolean;
}

type Props = StateProps & DispatchProps & OuterProps;

const columns: ColumnsType<TransferAccount> = [
  {
    title: "Name",
    key: "name",
    render: (text: any, record: any) =>
      `${record.first_name} ${record.last_name}`
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
      record.is_approved ? "Approved" : "Not Approved"
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
    let data: TransferAccount[] = this.props.orderedTransferAccounts
      .filter(
        (accountId: number) =>
          this.props.transferAccounts.byId[accountId] != undefined
      )
      .map((accountId: number) => {
        let transferAccount = this.props.transferAccounts.byId[accountId];
        let user = this.props.users.byId[transferAccount.primary_user_id];
        let token_symbol = maybe(this.props.tokens.byId, [
          transferAccount.token,
          "symbol"
        ]);

        return {
          key: accountId,
          first_name: user.first_name,
          last_name: user.last_name,
          created: transferAccount.created,
          balance: transferAccount.balance,
          is_approved: transferAccount.is_approved,
          token_symbol: token_symbol
        };
      });

    const { selectedRowKeys } = this.state;

    const { actionButtons } = this.props;

    const headerCheckbox = (
      <Checkbox
        checked={selectedRowKeys.length > 0}
        indeterminate={
          selectedRowKeys.length > 0 && selectedRowKeys.length < data.length
        }
        onChange={() => console.log("fooobooo")}
      />
    );

    const rowSelection = {
      onChange: this.onSelectChange,
      selectedRowKeys: selectedRowKeys,
      columnTitle: headerCheckbox
    };

    let actionButtonElems = actionButtons.map((button: ActionButton) => (
      <Button
        onClick={() => button.onClick(selectedRowKeys)}
        loading={button.loading || false}
        disabled={selectedRowKeys.length === 0}
        type="default"
        style={{ minWidth: "150px", margin: "0.5em" }}
      >
        {button.label}
      </Button>
    ));

    const hasSelected = selectedRowKeys.length > 0;
    return (
      <div>
        <div>
          {actionButtonElems}
          <span style={{ marginLeft: 8 }}>
            {hasSelected ? `${selectedRowKeys.length} Selected` : ""}
          </span>
        </div>
        <Table
          columns={columns}
          dataSource={data}
          rowSelection={rowSelection}
        />
      </div>
    );
  }
}

export default connect(mapStateToProps)(TransferAccountList);
