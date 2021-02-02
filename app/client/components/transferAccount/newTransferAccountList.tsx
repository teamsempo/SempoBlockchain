import * as React from "react";

import { Table, Button } from "antd";

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
}

interface ComponentState {
  selectedRowKeys: React.Key[];
}

interface TransferAccount {
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
    console.log("selectedRowKeys changed: ", selectedRowKeys);
    this.setState({ selectedRowKeys });
  };

  render() {
    const { selectedRowKeys } = this.state;
    const { actionButtons } = this.props;
    const rowSelection = {
      onChange: this.onSelectChange,
      selectedRowKeys: selectedRowKeys
    };

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
          token_symbol: token_symbol
        };
      });

    let buttonRow = actionButtons.map((button: ActionButton) => (
      <Button
        onClick={() => button.onClick(selectedRowKeys)}
        loading={button.loading || false}
        disabled={selectedRowKeys.length === 0}
        type="default"
        style={{ minWidth: "150px", padding: "1em" }}
      >
        {button.label}
      </Button>
    ));

    return (
      <div>
        {buttonRow}
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
