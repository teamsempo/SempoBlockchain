import * as React from "react";

import { Link } from "react-router-dom";

import { Table, Tag, Pagination, Space } from "antd";

import { ColumnsType } from "antd/es/table";

import { ReduxState } from "../../reducers/rootReducer";
import { connect } from "react-redux";
import { formatMoney } from "../../utils";
import DateTime from "../dateTime";

interface StateProps {
  users: any;
  tokens: any;
}

export interface OnPaginateChange {
  (page: number, pageSize: number | undefined): void;
}

export interface Pagination {
  currentPage: number;
  items: number;
  onChange: OnPaginateChange;
}

interface stringIndexable {
  [index: string]: any;
}

interface OuterProps extends stringIndexable {
  params: string;
  searchString: string;
  creditTransfers: ReduxState["creditTransfers"];
  users: ReduxState["users"];
}

export interface TransferAccount {
  id: string;
  created: string;
  amount: string;
  sender: string;
  recipient: string;
  transfer_type: string;
  approval: string;
  blockchain_approval: string;
  transfer_status_colour: string;
  blockchain_status_colour: string;
}

type Props = StateProps & OuterProps;

const columns: ColumnsType<TransferAccount> = [
  {
    title: "ID",
    key: "id",
    ellipsis: true,
    render: (text: any, record: any) => {
      const pathname_array = location.pathname.split("/").slice(1);
      const transferAccountID = parseInt(pathname_array[1]);
      const customRoutes = transferAccountID
        ? [
            { path: "", breadcrumbName: "Home" },
            { path: "accounts/", breadcrumbName: "Accounts" },
            {
              path: `accounts/${transferAccountID}`,
              breadcrumbName: `Transfer Account ${transferAccountID}`,
            },
            {
              path: `transfers/${record.id}`,
              breadcrumbName: `Transfer ${record.id}`,
            },
          ]
        : undefined;
      return (
        <Link
          to={{
            pathname: "/transfers/" + record.id,
            state: { customRoutes },
          }}
          style={{
            textDecoration: "underline",
            color: "#000000a6",
            fontWeight: 400,
          }}
        >
          {record.id}
        </Link>
      );
    },
  },
  {
    title: "Created",
    key: "created",
    render: (text: any, record: any) => (
      <DateTime created={record.created} useRelativeTime={false} />
    ),
  },
  {
    title: "Amount",
    key: "amount",
    render: (text: any, record: any) => {
      const money = formatMoney(
        record.amount / 100,
        undefined,
        undefined,
        undefined,
        record.token_symbol
      );
      return <p style={{ margin: 0 }}>{money}</p>;
    },
  },
  {
    title: "Sender",
    key: "sender_name",
    ellipsis: true,
    render: (text: any, record: any) => {
      const isDisbursement = record.transfer_type === "DISBURSEMENT";
      return (
        <Link
          to={
            isDisbursement
              ? "#"
              : "/accounts/" + record.sender_transfer_account_id
          }
          style={{
            textDecoration: isDisbursement ? "" : "underline",
            color: "#000000a6",
            fontWeight: 400,
          }}
        >
          {record.sender_name}
        </Link>
      );
    },
  },
  {
    title: "Recipient",
    key: "recipient_name",
    ellipsis: true,
    render: (text: any, record: any) => {
      const isReclamation = record.transfer_type === "RECLAMATION";
      return (
        <Link
          to={
            isReclamation
              ? "#"
              : "/accounts/" + record.recipient_transfer_account_id
          }
          style={{
            textDecoration: isReclamation ? "" : "underline",
            color: "#000000a6",
            fontWeight: 400,
          }}
        >
          {record.recipient_name}
        </Link>
      );
    },
  },
  {
    title: "Type",
    key: "transfer_type",
    ellipsis: true,
    render: (text: any, record: any) => <>{record.transfer_type}</>,
  },
  {
    title: "Approval",
    key: "transfer_status",
    ellipsis: true,
    render: (text: any, record: any) => (
      <Tag color={record.transfer_status_colour}>{record.transfer_status}</Tag>
    ),
  },
  {
    title: "Blockchain",
    key: "blockchain_status",
    ellipsis: true,
    render: (text: any, record: any) => (
      <Tag color={record.blockchain_status_colour}>
        {record.blockchain_status}
      </Tag>
    ),
  },
];

const mapStateToProps = (state: ReduxState): StateProps => {
  return {
    tokens: state.tokens,
    users: state.users,
  };
};

class CreditTransferList extends React.Component<Props> {
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
      searchString: this.props.searchString,
    });
  }

  render() {
    const {} = this.state;
    const { creditTransfers, users } = this.props;

    let data: any[] = Object.values(creditTransfers.byId)
      .map((transfer: any) => {
        let sender_name;
        let recipient_name;
        const recipient_user =
          transfer.recipient_user && users.byId[transfer.recipient_user];

        const sender_user =
          transfer.sender_user && users.byId[transfer.sender_user];

        let email = transfer.authorising_user_email;

        sender_name = sender_user
          ? (sender_user.first_name === null ? "" : sender_user.first_name) +
            " " +
            (sender_user.last_name === null ? "" : sender_user.last_name)
          : "Transfer Account " + transfer.sender_transfer_account_id;

        recipient_name = recipient_user
          ? (recipient_user.first_name === null
              ? ""
              : recipient_user.first_name) +
            " " +
            (recipient_user.last_name === null ? "" : recipient_user.last_name)
          : "Transfer Account " + transfer.recipient_transfer_account_id;

        if (transfer.transfer_type === "DISBURSEMENT") {
          sender_name = email || "Administrator";
        } else if (transfer.transfer_type === "RECLAMATION") {
          recipient_name = email || "Administrator";
        }

        if (transfer.transfer_status === "COMPLETE") {
          var transfer_status_colour = "#9BDF56";
        } else if (transfer.transfer_status === "PENDING") {
          transfer_status_colour = "#F5A623";
        } else if (transfer.transfer_status === "PARTIAL") {
          transfer_status_colour = "#d48806";
        } else if (transfer.transfer_status === "REJECTED") {
          transfer_status_colour = "#F16853";
        } else {
          transfer_status_colour = "#c6c6c6";
        }

        if (transfer.blockchain_status === "COMPLETE") {
          var blockchain_status_colour = "#9BDF56";
        } else if (transfer.blockchain_status === "PENDING") {
          blockchain_status_colour = "#F5A623";
        } else if (transfer.blockchain_status === "PARTIAL") {
          blockchain_status_colour = "#d48806";
        } else if (transfer.blockchain_status === "UNSTARTED") {
          blockchain_status_colour = "#F16853";
        } else if (transfer.blockchain_status === "ERROR") {
          blockchain_status_colour = "#F16853";
        } else {
          blockchain_status_colour = "#c6c6c6";
        }
        return {
          id: transfer.id,
          created: transfer.created,
          amount: transfer.transfer_amount,
          transfer_status: transfer.transfer_status,
          transfer_status_colour: transfer_status_colour,
          transfer_type: transfer.transfer_type,
          blockchain_status: transfer.blockchain_status,
          blockchain_status_colour: blockchain_status_colour,
          recipient_name: recipient_name,
          sender_name: sender_name,
          sender_transfer_account_id: transfer.sender_transfer_account_id,
          recipient_transfer_account_id: transfer.recipient_transfer_account_id,
        };
      })
      .reverse();
    return (
      <div style={{ opacity: this.props.disabled ? 0.6 : 1 }}>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            flexWrap: "wrap",
          }}
        >
          <div
            style={{ display: "flex", alignItems: "center", minHeight: "25px" }}
          ></div>
          <div
            style={{
              display: "flex",
              alignItems: "flex-end",
              minHeight: "25px",
            }}
          ></div>
        </div>
        <Space direction="vertical">
          <Table
            loading={creditTransfers.loadStatus.isRequesting}
            columns={columns}
            dataSource={data}
            style={{ marginLeft: "10px", marginRight: "10px" }}
            pagination={this.props.paginationOptions ? false : undefined}
          />
          {this.props.paginationOptions ? (
            <Pagination
              style={{ display: "flex", justifyContent: "flex-end" }}
              current={this.props.paginationOptions.currentPage}
              showSizeChanger
              defaultCurrent={1}
              defaultPageSize={10}
              total={this.props.paginationOptions.items}
              onChange={this.props.paginationOptions.onChange}
              showTotal={(total, range) =>
                `${range[0]}-${range[1]} of ${total} items`
              }
            />
          ) : (
            <></>
          )}
        </Space>
      </div>
    );
  }
}

export default connect(mapStateToProps)(CreditTransferList);
