import * as React from "react";

import { Link } from "react-router-dom";

import { Table, Tag, Pagination, Space } from "antd";

import { ColumnsType } from "antd/es/table";

import { ReduxState } from "../../reducers/rootReducer";
import { connect } from "react-redux";
import { formatMoney } from "../../utils";
import DateTime from "../dateTime";

interface StateProps {
  transferAccounts: any;
  users: any;
  tokens: any;
}

export interface OnPaginateChange {
  (
    page: number,
    pageSize: number | undefined
  ): void;
}

export interface Pagination {
  currentPage: number,
  items: number,
  onChange: OnPaginateChange;
}

interface stringIndexable {
  [index: string]: any;
}

interface OuterProps extends stringIndexable {
  params: string;
  searchString: string;
  orderedTransferAccounts: number[];
  users: any;
}

export interface TransferAccount {
  key: number;
  first_name: string;
  last_name: string;
  created: string;
  balance: number;
  token_symbol: string;
}

type Props = StateProps & OuterProps;

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
    render: (text: any, record: any) => <DateTime created={record.created} useRelativeTime={false} />
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
      loadedPages: [1],
      params: "",
      searchString: "",
    };
  }

  componentDidMount() {
    this.setState({
      params: this.props.params,
      searchString: this.props.searchString
    })
  }

  render() {
    const { } = this.state;
    const {
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
        let token_symbol = tokens.byId[transferAccount.token]?.symbol;

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


    return (
      <div style={{opacity: this.props.disabled? 0.6 : 1}}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            flexWrap: "wrap"
          }}
        >
          <div
            style={{ display: "flex", alignItems: "center", minHeight: "25px" }}
          >
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "flex-end",
              minHeight: "25px"
            }}
          >
          </div>
        </div>
        <Space direction="vertical">
          <Table
            loading={transferAccounts.loadStatus.isRequesting}
            columns={columns}
            dataSource={data}
            style={{ marginLeft: "10px", marginRight: "10px" }}
            pagination={this.props.paginationOptions? false: undefined}
          />
          { this.props.paginationOptions?
            <Pagination
              style={{display: 'flex', justifyContent: 'flex-end'}}
              current={this.props.paginationOptions.currentPage}
              showSizeChanger
              defaultCurrent={1}
              defaultPageSize={10}
              total={this.props.paginationOptions.items}
              onChange={this.props.paginationOptions.onChange}
              showTotal={(total, range) => `${range[0]}-${range[1]} of ${total} items`}
            />
            : <></>
          }
        </Space>
      </div>
    );
  }
}

export default connect(mapStateToProps)(TransferAccountList);
