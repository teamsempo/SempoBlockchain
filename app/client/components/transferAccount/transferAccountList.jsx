import React from 'react';
import { connect } from 'react-redux';
import styled from 'styled-components';
import ReactTable from 'react-table'
import { browserHistory } from '../../app.jsx'

import { ModuleBox, TopRow, StyledButton, StyledSelect, Wrapper } from '../styledElements.js'

import LoadingSpinner from "../loadingSpinner.jsx";
import DateTime from '../dateTime.jsx';
import NewTransferManager from '../management/newTransferManager.jsx'

import { formatMoney } from "../../utils";
import { editTransferAccount, setSelected } from "../../reducers/transferAccountReducer";
import {TransferAccountTypes} from "../transferAccount/types";

const mapStateToProps = (state) => {
  return {
    login: state.login,
    transferAccounts: state.transferAccounts,
    creditTransfers: state.creditTransfers,
  };
};

const mapDispatchToProps = (dispatch) => {
  return{
    editTransferAccountRequest: (body) => dispatch(editTransferAccount({body})),
    setSelected: (selected) => dispatch(setSelected(selected)),
  };
};

class TransferAccountList extends React.Component {
  // ---- INFO ----
  // TransferAccountList accepts;
  // transfer_account_list (pass in as item_list)
  //    + array of transfer account objects
  //    + filterable and searchable via SearchBoxWithFilter
  constructor() {
	super();
	this.state = {
	  data: [],
	  loading: true,
	  user_id: null,
    transfer_account_ids: {},
    allCheckedTransferAccounts: false,
    newTransfer: false,
    account_type: 'ALL',
	};
	this.handleChange = this.handleChange.bind(this);
	this.checkAllTransferAccounts = this.checkAllTransferAccounts.bind(this);
	this.toggleSelectedTransferAccount = this.toggleSelectedTransferAccount.bind(this);
	this.onNewTransfer = this.onNewTransfer.bind(this);
	this.approveSelected = this.approveSelected.bind(this);
  }

  componentDidMount() {
    if (this.props.item_list !== undefined) {
      this.props.item_list.map(i => {
        this.setState(prevState => ({
          transfer_account_ids: {
            ...prevState.transfer_account_ids,
            [i.id]: false,
          }
        }))
      });
    }
  }

  componentWillUnmount() {
    let selected = [];
    Object.keys(this.state.transfer_account_ids).map(id => {
      if (this.state.transfer_account_ids[id]) selected.push(id);
    })

    this.props.setSelected(selected)
  }

  componentDidUpdate(newProps) {
    if (this.props.creditTransfers.createStatus.success !== newProps.creditTransfers.createStatus.success) {
      this.setState({newTransfer: false});
    }

    if (this.props.item_list !== undefined && this.props.item_list !== newProps.item_list) {
      this.props.item_list.map(i => {
        this.setState(prevState => ({
          transfer_account_ids: {
            ...prevState.transfer_account_ids,
            [i.id]: false,
          },
          allCheckedTransferAccounts: false,
        }))
      });
    }
  }

  get_selected_ids_array(selected) {
    Object.filter = (obj, predicate) => Object.keys(obj).filter( key => predicate(obj[key]) ).reduce( (res, key) => (res[key] = obj[key], res), {} );

    return Object.keys(Object.filter(selected, selected => selected === true));
  }

  toggleSelectedTransferAccount(id) {
    const value = !this.state.transfer_account_ids[id];

     this.setState(prevState => ({
         transfer_account_ids: {
             ...prevState.transfer_account_ids,
             [id]: value
         },
         allCheckedTransferAccounts: false,
     }))
  }

  displaySelect(id) {
    if (this.state.transfer_account_ids[id] !== null) {
        return(
            <input name={id} type="checkbox" checked={this.state.transfer_account_ids[id]} onChange={() => this.toggleSelectedTransferAccount(id)} />
        )
    }
  }

  checkAllTransferAccounts(filteredData) {
      if (this.state.allCheckedTransferAccounts) {
          // UNCHECK
          var value = false
      } else {
          // CHECK ALL
          value = true
      }

      filteredData.map(i => {
         this.setState(prevState => ({
             transfer_account_ids: {
                 ...prevState.transfer_account_ids,
                 [i.id]: value
             },
             allCheckedTransferAccounts: value,
         }))
      })
  };

  onNewTransfer() {
    this.setState(prevState => ({
      newTransfer: !prevState.newTransfer
    }));
  }

  approveSelected() {
    let approve = true;
    let transfer_account_id_list = this.get_selected_ids_array(this.state.transfer_account_ids);

    this.props.editTransferAccountRequest(
        {
            transfer_account_id_list,
            approve,
        },
    );
  }

  handleChange (evt) {
    this.setState({ [evt.target.name]: evt.target.value });
  }

  _customName(transferAccount) {
    if (this.props.login.adminTier === 'view' && typeof(transferAccount.blockchain_address) !== "undefined") {
      return transferAccount.blockchain_address
    }
    return (transferAccount.first_name === null ? '' : transferAccount.first_name) + ' ' + (transferAccount.last_name === null ? '' : transferAccount.last_name)
  }

  render() {
    const {account_type} = this.state;
    const loadingStatus = this.props.transferAccounts.loadStatus.isRequesting;
    let accountTypes = Object.keys(TransferAccountTypes);
    accountTypes.push('ALL'); // filter should have all option

    var filteredData = this.props.item_list !== undefined ? this.props.item_list : null;

    if (account_type !== 'ALL') {
      // a filter is being applied
      if (account_type === TransferAccountTypes.USER) {
        filteredData = filteredData.filter(account => account.is_beneficiary)
      } else if (account_type === TransferAccountTypes.VENDOR || account_type === TransferAccountTypes.CASHIER) {
        filteredData = filteredData.filter(account => account.is_vendor)
      } else if (account_type === TransferAccountTypes.TOKENAGENT) {
        filteredData = filteredData.filter(account => account.is_tokenagent)
      } else if (account_type === TransferAccountTypes.GROUPACCOUNT) {
        filteredData = filteredData.filter(account => account.is_groupaccount)
      }
    }

	  let rowValues = Object.values(this.state.transfer_account_ids);
    let numberSelected = rowValues.filter(Boolean).length;
    let isSelected = numberSelected > 0;

    if (isSelected) {
        var topBarContent =
            <div style={{display: 'flex', justifyContent: 'space-between', width: '100%'}}>
              <p style={{margin: '1em'}}>{numberSelected} selected</p>

              {this.props.login.adminTier !== 'view' ?
              <div style={{margin: '1em 0', display: 'flex'}}>
                  <StyledButton onClick={this.onNewTransfer} style={{display: (this.state.newTransfer ? 'none' : 'flex'), fontWeight: '400', margin: '0em 1em', lineHeight: '25px', height: '25px'}}>NEW TRANSFER</StyledButton>
                  <StyledButton onClick={this.approveSelected} style={{display: (this.state.newTransfer ? 'none' : 'flex'), fontWeight: '400', margin: '0em 1em 0 0', lineHeight: '25px', height: '25px'}}>APPROVE</StyledButton>
                  <UploadButtonWrapper style={{marginRight: 0, marginLeft: 0}}>
                    <StyledButton onClick={() => browserHistory.push('/export')} style={{fontWeight: '400', margin: '0em 1em 0 0', lineHeight: '25px', height: '25px'}}>
                        Export
                    </StyledButton>
                  </UploadButtonWrapper>
              </div> : null}

            </div>

    } else {
        topBarContent =
            <div style={{display: 'flex', justifyContent: 'space-between', width: '100%'}}>
              <StyledSelect style={{fontWeight: '400', margin: '1em', lineHeight: '25px', height: '25px'}} name="account_type" value={this.state.account_type} onChange={this.handleChange}>
                {accountTypes.map((accountType, index) => {
                  return <option key={index} name="account_type" value={accountType}>{accountType}</option>
                })}
              </StyledSelect>

              {this.props.login.adminTier !== 'view' ?
              <div style={{display: 'flex', flexDirection: 'row'}}>
                  <UploadButtonWrapper style={{marginRight: 0, marginLeft: 0}}>
                      <StyledButton onClick={() => browserHistory.push('/create')} style={{fontWeight: '400', margin: '0em 1em', lineHeight: '25px', height: '25px'}}>
                          + Add New
                      </StyledButton>
                  </UploadButtonWrapper>
                  <UploadButtonWrapper style={{marginRight: 0, marginLeft: 0}}>
                      <StyledButton onClick={() => browserHistory.push('/export')} style={{fontWeight: '400', margin: '0em 1em 0 0', lineHeight: '25px', height: '25px'}}>
                          Export
                      </StyledButton>
                  </UploadButtonWrapper>
              </div> : null}

            </div>
    }

    if (this.state.newTransfer) {
        var newTransfer = <NewTransferManager transfer_account_ids={this.get_selected_ids_array(this.state.transfer_account_ids)} cancelNewTransfer={() => this.onNewTransfer()} />
    } else {
        newTransfer = null;
    }

    if (this.props.transferAccounts.loadStatus.isRequesting) {
      return (
        <div style={{display: 'flex', justifyContent: 'center', margin: '1em'}}>
          <LoadingSpinner/>
        </div>
      )
    }

	  if (this.props.transferAccounts.loadStatus.success && filteredData !== null && filteredData !== undefined) {

	    const tableLength = filteredData.length;

	    return (
        <div style={{display: 'flex', flexDirection: 'column'}}>
          {newTransfer}

            <ModuleBox style={{width: 'calc(100% - 2em)'}}>
              <Wrapper>
                <TopRow>
                  {topBarContent}
                </TopRow>
                <ReactTable
                  columns={[
                    {
                      Header: "",
                      accessor: "is_vendor",
                      headerClassName: 'react-table-header',
                      width: 40,
                      sortable: false,
                      Cell: cellInfo => (cellInfo.value === true ? <UserSVG src="/static/media/store.svg"/> : <UserSVG src="/static/media/user.svg"/>),
                    },
                    {
                      Header: "Name",
                      id: 'transferAccountName',
                      accessor: transferAccount => this._customName(transferAccount),
                      headerClassName: 'react-table-header',
                      className: 'react-table-first-cell',
                    },
                    {
                      Header: "Created",
                      accessor: "created",
                      headerClassName: 'react-table-header',
                      Cell: cellInfo => (<DateTime created={cellInfo.value}/>),
                    },
                    {
                      Header: "Balance",
                      accessor: "balance",
                      headerClassName: 'react-table-header',
                      Cell: cellInfo => {
                        const token = cellInfo.original.token && cellInfo.original.token.symbol;
                        const money = formatMoney(cellInfo.value / 100, undefined, undefined, undefined, token);
                        return <p style={{margin: 0}}>{money}</p>
                      },
                    },
                    {
                      Header: "Status",
                      accessor: "is_approved",
                      headerClassName: 'react-table-header',
                      Cell: cellInfo => (<p style={{margin: 0}}>{cellInfo.value === true ? 'Approved' : 'Unapproved'}</p>)
                    },
                    {
                      Header: () => (<input type="checkbox" checked={this.state.allCheckedTransferAccounts} onChange={() => this.checkAllTransferAccounts(filteredData)}/>),
                      accessor: "id",
                      headerClassName: 'react-table-header',
                      width: 60,
                      sortable: false,
                      Cell: cellInfo => this.displaySelect(cellInfo.value)
                    },
                  ]}
                  loading={loadingStatus} // Display the loading overlay when we need it
                  data={filteredData}
                  pageSize={tableLength}
                  sortable={true}
                  showPagination={false}
                  showPageSizeOptions={false}
                  className='react-table'
                  resizable={false}
                  getTdProps={(state, rowInfo, column) => {
                    return {
                      onClick: (e, handleOriginal) => {
                        // handle click on checkbox
                        if (column.id === "id") {
                            this.toggleSelectedTransferAccount(rowInfo.original.id);
                            return
                        }

                        browserHistory.push('/accounts/' + rowInfo.row.id);

                        if (handleOriginal) {
                          handleOriginal();
                        }
                      }
                    };
                  }}
                />
                <FooterBar>
                    <p style={{margin: 0}}>{tableLength} accounts</p>
                </FooterBar>
              </Wrapper>
            </ModuleBox>
        </div>
      );
	  }

	  return(
	    <ModuleBox>
			  <p style={{padding: '1em', textAlign: 'center'}}>No transfer accounts found</p>
      </ModuleBox>
	  )
  }
};

export default connect(mapStateToProps, mapDispatchToProps)(TransferAccountList);

const FooterBar = styled.div`
    border-top: solid 1px rgba(0,0,0,0.05);
    padding: 1em;
`;

const UserSVG = styled.img`
  width: 20px;
  height: 20px;
`;

const UploadButtonWrapper = styled.div`
  margin: auto 1em;
`;