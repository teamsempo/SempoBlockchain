import * as React from "react";

import { Link } from "react-router-dom";

import { Table, Button, Checkbox, Tag, Pagination, Space, Alert } from "antd";

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

interface DispatchProps {}

export interface OnSelectChange {
  (
    selectedRowKeys: React.Key[],
    unselectedRowKeys: React.Key[],
    allSelected: boolean
  ): void;
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
  orderedTransferAccounts: number[];
  users: any;
  actionButtons: ActionButton[];
  dataButtons: DataButton[];
  onSelectChange?: OnSelectChange;
  paginationOptions?: Pagination;
  providedSelectedRowKeys?: React.Key[];
  providedUnselectedRowKeys?: React.Key[];
}

interface ComponentState extends stringIndexable {
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

export interface DataButton {
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
          fontWeight: 400,
        }}
      >
        {record.first_name} {record.last_name}
      </Link>
    ),
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
    },
  },
  {
    title: "Status",
    key: "status",
    render: (text: any, record: any) =>
      record.is_approved ? (
        <Tag color="#9bdf56">Approved</Tag>
      ) : (
        <Tag color="#ff715b">Not Approved</Tag>
      ),
  },
];

const mapStateToProps = (state: ReduxState): StateProps => {
  return {
    login: state.login,
    tokens: state.tokens,
    transferAccounts: state.transferAccounts,
    users: state.users,
  };
};

class TransferAccountList extends React.Component<Props, ComponentState> {
  constructor(props: Props) {
    super(props);

    this.state = {
      selectedRowKeys: [],
      unselectedRowKeys: [],
      allSelected: false,
      loadedPages: [1],
      allLoadedRows: [],
      params: "",
      searchString: "",
    };
  }

  componentDidMount() {
    let unselectedKeys =
      this.props.providedUnselectedRowKeys || this.state.unselectedRowKeys;
    let selectedKeys =
      this.props.providedSelectedRowKeys || this.state.selectedRowKeys;
    if (unselectedKeys.length > 0) {
      selectedKeys = this.props.orderedTransferAccounts.filter(
        (accountId: number) =>
          this.props.transferAccounts.byId[accountId] != undefined &&
          !unselectedKeys.includes(accountId)
      );
    }

    this.setState({
      selectedRowKeys: selectedKeys,
      unselectedRowKeys: unselectedKeys,
      params: this.props.params,
      searchString: this.props.searchString,
    });
  }

  componentDidUpdate(prevProps: Props) {
    if (
      this.props.transferAccounts.IdList !== prevProps.transferAccounts.IdList
    ) {
      if (
        this.state.allSelected &&
        !this.state.loadedPages.includes(
          this.props.paginationOptions?.currentPage
        )
      ) {
        this.setState({
          loadedPages: [
            ...this.state.loadedPages,
            this.props.paginationOptions?.currentPage,
          ],
        });
        this.setState({
          allLoadedRows: [
            ...new Set([
              ...this.state.allLoadedRows,
              ...this.props.orderedTransferAccounts,
            ]),
          ],
        });
        this.setState({
          selectedRowKeys: [
            ...new Set([
              ...this.state.selectedRowKeys,
              ...this.props.transferAccounts.IdList,
            ]),
          ],
        });
      }
    }
    if (
      this.props.params !== prevProps.params ||
      this.props.searchString !== prevProps.searchString
    ) {
      this.setState({
        allSelected: false,
        selectedRowKeys: [],
        unselectedRowKeys: [],
        loadedPages: [1],
        allLoadedRows: [],
      });
    }
  }

  onChange = (
    selectedRowKeys: React.Key[],
    selectedRows: TransferAccount[]
  ) => {
    if (this.props.disabled) {
      return;
    }
    const allLoadedRows = [
      ...new Set([
        ...this.state.allLoadedRows,
        ...this.props.orderedTransferAccounts,
      ]),
    ];
    let unselectedRowKeys: React.Key[] = [];

    if (this.state.allSelected) {
      // We only define the unselected rows when the "select all" box has been flagged as true (ie a "default selected" state),
      // because unselected rows isn't specific enough when you start from a "default unselected" state
      let selectedSet = new Set(selectedRowKeys);
      unselectedRowKeys = allLoadedRows.filter((row) => !selectedSet.has(row));
    }

    this.setState(
      { selectedRowKeys, unselectedRowKeys },
      this.onSelectChangeCallback
    );
  };

  toggleSelectAll = (keys: React.Key[], data: TransferAccount[]) => {
    if (this.props.disabled) {
      return;
    }

    if (keys.length === data.length) {
      this.setState(
        {
          loadedPages: [1],
          allLoadedRows: [],
          selectedRowKeys: [],
          unselectedRowKeys: [],
          allSelected: false,
        },
        this.onSelectChangeCallback
      );
    } else {
      this.setState(
        {
          loadedPages: [1],
          allLoadedRows: [],
          selectedRowKeys: data.map((r) => r.key),
          unselectedRowKeys: [],
          allSelected: true,
        },
        this.onSelectChangeCallback
      );
    }
  };

  toggleUnselect = () => {
    this.setState(
      {
        loadedPages: [1],
        allLoadedRows: [],
        selectedRowKeys: [],
        unselectedRowKeys: [],
        allSelected: false,
      },
      this.onSelectChangeCallback
    );
  };

  onSelectChangeCallback() {
    if (this.props.onSelectChange) {
      // after setting the state
      // transparently pass through the callback to parent, in case it's needed there
      this.props.onSelectChange(
        this.state.selectedRowKeys,
        this.state.unselectedRowKeys,
        this.state.allSelected
      );
    }
  }

  render() {
    const { selectedRowKeys, unselectedRowKeys, allSelected } = this.state;
    const {
      actionButtons,
      dataButtons,
      orderedTransferAccounts,
      transferAccounts,
      users,
      tokens,
    } = this.props;
    let data: TransferAccount[] = orderedTransferAccounts
      .filter(
        (accountId: number) => transferAccounts.byId[accountId] != undefined
      )
      .map((accountId: number) => {
        let transferAccount = transferAccounts.byId[accountId];
        let user = users.byId[transferAccount.primary_user_id];
        let token_symbol = tokens.byId[transferAccount.token]?.symbol;
        if (user == undefined) {
          user = {
            first_name: transferAccount.blockchain_address,
            last_name: "",
            is_vendor: transferAccount.is_vendor,
            is_beneficiary: transferAccount.is_beneficiary,
          };
        }
        return {
          key: accountId,
          first_name: user.first_name || "",
          last_name: user.last_name || "",
          is_vendor: user.is_vendor,
          is_beneficiary: user.is_beneficiary,
          created: transferAccount.created,
          balance: transferAccount.balance,
          is_approved: transferAccount.is_approved,
          token_symbol: token_symbol,
        };
      });

    const headerCheckbox = (
      <Checkbox
        checked={selectedRowKeys.length > 0}
        indeterminate={
          allSelected
            ? unselectedRowKeys.length > 0
            : selectedRowKeys.length > 0
        }
        onChange={(e) => this.toggleSelectAll(selectedRowKeys, data)}
      />
    );

    const rowSelection = {
      onChange: this.onChange,
      selectedRowKeys: selectedRowKeys,
      columnTitle: headerCheckbox,
      preserveSelectedRowKeys: true,
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

    let dataButtonsElems = dataButtons.map((button: DataButton) => (
      <Button
        key={button.label}
        onClick={() => button.onClick()}
        loading={button.loading || false}
        type="default"
        style={{ minWidth: "150px", margin: "10px" }}
      >
        {button.label}
      </Button>
    ));

    const hasSelected = selectedRowKeys.length > 0;
    const numberSelected = this.props.paginationOptions?.items
      ? allSelected
        ? this.props.paginationOptions?.items - unselectedRowKeys.length
        : selectedRowKeys.length
      : selectedRowKeys.length;
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
          >
            {actionButtonElems}
          </div>
          <div
            style={{
              display: "flex",
              alignItems: "flex-end",
              minHeight: "25px",
            }}
          >
            {dataButtonsElems}
          </div>
        </div>
        <Space direction="vertical">
          {hasSelected ? (
            <Alert
              message={`${numberSelected} Selected`}
              style={{ marginLeft: "10px", marginRight: "10px" }}
              closeText="Clear"
              onClose={this.toggleUnselect}
            />
          ) : null}
          <Table
            loading={transferAccounts.loadStatus.isRequesting}
            columns={columns}
            dataSource={data}
            rowSelection={rowSelection}
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

export default connect(mapStateToProps)(TransferAccountList);
