import * as React from "react";

import { Link } from "react-router-dom";

import { Table, Tag } from "antd";

import { ColumnsType } from "antd/es/table";

import { ReduxState, sempoObjects } from "../../reducers/rootReducer";
import { connect } from "react-redux";
import DateTime from "../dateTime";
import { apiActions, LoadRequestAction } from "../../genericState";
import { formatMoney, getActiveToken, toCurrency } from "../../utils";

interface StateProps {
  bulkTransfers: any;
  activeToken: any;
}

interface DispatchProps {
  loadBulkTransfers: () => LoadRequestAction;
}

interface OuterProps {}

interface ComponentState {}

export interface BulkTransfer {
  label: string;
  key: number;
  disbursement_amount: number;
  recipient_count: number;
  state: string;
  created: string;
}

type Props = StateProps & DispatchProps & OuterProps;

const columns: ColumnsType<BulkTransfer> = [
  {
    title: "ID",
    key: "ID",
    ellipsis: true,
    render: (text: any, record: any) => (
      <Link
        to={"/bulk/" + record.key}
        style={{
          textDecoration: "underline",
          color: "#000000a6",
          fontWeight: 400
        }}
      >
        {`${record.key}`}
      </Link>
    )
  },
  {
    title: "Label",
    key: "Label",
    render: (text: any, record: any) => record.label
  },
  {
    title: "Created",
    key: "created",
    render: (text: any, record: any) => (
      <DateTime created={record.created} useRelativeTime={false} />
    )
  },
  {
    title: "Recipient Count",
    key: "Count",
    render: (text: any, record: any) => record.recipient_count
  },
  {
    title: "Transfer Type",
    key: "Type",
    render: (text: any, record: any) => record.type
  },
  {
    title: "Transfer Amount",
    key: "amount",
    render: (text: any, record: any) =>
      formatMoney(
        toCurrency(record.disbursement_amount),
        undefined,
        undefined,
        undefined,
        record.symbol
      )
  },
  {
    title: "Status",
    key: "status",
    render: (text: any, record: any) => {
      if (record.state === "APPROVED") {
        return <Tag color="#9bdf56">Approved</Tag>;
      } else if (record.state === "PENDING") {
        return <Tag color="#e2a963">Pending</Tag>;
      } else if (record.state === "PARTIAL") {
        return <Tag color="#d48806">Partial</Tag>;
      } else {
        return <Tag color="#f16853">Rejected</Tag>;
      }
    }
  }
];

const mapStateToProps = (state: ReduxState): StateProps => {
  return {
    bulkTransfers: state.bulkTransfers,
    activeToken: getActiveToken(state)
  };
};

const mapDispatchToProps = (dispatch: any): DispatchProps => {
  return {
    loadBulkTransfers: () =>
      dispatch(apiActions.load(sempoObjects.bulkTransfers))
  };
};

class BulkTransferList extends React.Component<Props, ComponentState> {
  constructor(props: Props) {
    super(props);

    this.state = {};
  }

  componentDidMount() {
    this.props.loadBulkTransfers();
  }

  render() {
    const { bulkTransfers } = this.props;

    let data: BulkTransfer[] = bulkTransfers.idList
      .filter((id: number) => bulkTransfers.byId[id] != undefined)
      .map((id: number) => {
        let bulkTransfer = bulkTransfers.byId[id];

        return {
          key: id,
          label: bulkTransfer.label,
          disbursement_amount: bulkTransfer.disbursement_amount,
          recipient_count: bulkTransfer.recipient_count,
          state: bulkTransfer.state,
          type: bulkTransfer.transfer_type,
          created: bulkTransfer.created,
          symbol: this.props.activeToken.symbol
        };
      });

    return (
      <Table
        loading={bulkTransfers.loadStatus.isRequesting}
        columns={columns}
        dataSource={data}
        style={{ marginLeft: "10px", marginRight: "10px" }}
      />
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(BulkTransferList);
