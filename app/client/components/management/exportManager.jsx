import React from 'react';
import { connect } from 'react-redux';
import styled from 'styled-components';
import { DateRangePicker } from 'react-dates';

import AsyncButton from '../AsyncButton.jsx';

import { newExport, RESET_EXPORT } from '../../reducers/exportReducer';

import {
  Input,
  StyledButton,
  ErrorMessage,
  ModuleHeader,
  StyledSelect,
  ModuleBox,
} from '../styledElements';

const mapStateToProps = state => ({
  newExportRequest: state.newExportRequest,
  selectedTransferAccounts: state.transferAccounts.selected,
});

const mapDispatchToProps = dispatch => ({
  resetExport: () => {
    dispatch({ type: RESET_EXPORT });
  },
  newExport: body => dispatch(newExport({ body })),
});

class ExportManager extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      error_message: '',
      date_range: 'all',
      includeTransfers: false,
      customExportCycle: false,
      startDate: null,
      endDate: null,
      account_type: 'VENDOR',
    };
    this.handleInputChange = this.handleInputChange.bind(this);
    this.handleChange = this.handleChange.bind(this);
  }

  componentWillUnmount() {
    this.resetCreateTransferAccount();
  }

  resetCreateTransferAccount() {
    this.props.resetExport();
  }

  handleInputChange(event) {
    const { target } = event;
    const { value } = target;
    const { name } = target;

    this.setState({
      [name]: value,
      error_message: '',
    });
  }

  handleChange(evt) {
    this.setState({ [evt.target.name]: evt.target.value });
  }

  handleToggle(evt, props) {
    this.setState({ [evt.target.name]: !props });
  }

  attemptNewExport() {
    if (this.state.account_type === 'VENDOR') {
      var user_type = 'vendor';
    } else if (this.state.account_type === 'SELECTED') {
      user_type = 'selected';
    } else {
      user_type = 'beneficiary';
    }

    if (this.state.customExportCycle === true) {
      var payable_period_start_date = this.state.startDate;
      var payable_period_end_date = this.state.endDate;
    } else {
      payable_period_start_date = null;
      payable_period_end_date = null;
    }

    this.props.newExport({
      export_type: '',
      include_transfers: this.state.includeTransfers,
      user_type,
      date_range: this.state.date_range,
      payable_period_start_date,
      payable_period_end_date,
      selected: this.props.selectedTransferAccounts,
    });
  }

  render() {
    if (this.state.customExportCycle) {
      var customExportCycle = (
        <div>
          <DateRangePicker
            startDate={this.state.startDate} // momentPropTypes.momentObj or null,
            startDateId="your_unique_start_date_id" // PropTypes.string.isRequired,
            endDate={this.state.endDate} // momentPropTypes.momentObj or null,
            endDateId="your_unique_end_date_id" // PropTypes.string.isRequired,
            onDatesChange={({ startDate, endDate }) =>
              this.setState({ startDate, endDate })
            } // PropTypes.func.isRequired,
            focusedInput={this.state.focusedInput} // PropTypes.oneOf([START_DATE, END_DATE]) or null,
            onFocusChange={focusedInput => this.setState({ focusedInput })} // PropTypes.func.isRequired,
            withPortal
            hideKeyboardShortcutsPanel
            isOutsideRange={() => false}
          />
        </div>
      );
    } else {
      customExportCycle = null;
    }

    return (
      <div>
        <ModuleHeader>EXPORT ACCOUNTS</ModuleHeader>
        <div style={{ margin: '1em' }}>
          {/* <div style={{display: 'flex', flexDirection: 'row', padding: '1em 0'}}> */}
          {/* <p style={{margin: '0 1em 0 0'}}>Date Range:</p> */}
          {/* <StyledSelect style={{fontWeight: '400', margin: '0', lineHeight: '25px', height: '25px'}} name="date_range" defaultValue="all" */}
          {/* onChange={this.handleChange}> */}
          {/* <option name="date_range" value="all">All</option> */}
          {/* <option name="date_range" value="day">Previous Day</option> */}
          {/* <option name="date_range" value="week">Previous Week</option> */}
          {/* </StyledSelect> */}
          {/* </div> */}
          <div
            style={{ display: 'flex', flexDirection: 'row', padding: '1em 0' }}>
            <p style={{ margin: '0px 1em 0px 0px' }}>Export:</p>
            <StyledSelect
              style={{
                fontWeight: '400',
                margin: '0 1em',
                lineHeight: '25px',
                height: '25px',
              }}
              name="account_type"
              value={this.state.account_type}
              onChange={this.handleChange}>
              <option name="account_type" value="VENDOR">
                VENDORS
              </option>
              <option name="account_type" value={window.BENEFICIARY_TERM}>
                {window.BENEFICIARY_TERM_PLURAL}
              </option>
              <option name="account_type" value="SELECTED">
                SELECTED
              </option>
            </StyledSelect>
          </div>
          {/* <div> */}
          {/* <div style={{display: 'flex', flexDirection: 'row', padding: '1em 0'}}> */}
          {/* <p style={{margin: '0 1em 0 0'}}>Custom Export Cycle?</p><input name='customExportCycle' type="checkbox" checked={this.state.customExportCycle} onChange={(evt) => this.handleToggle(evt, this.state.customExportCycle)}/> */}
          {/* </div> */}
          {/* {customExportCycle} */}
          {/* </div> */}
          <div
            style={{ display: 'flex', flexDirection: 'row', padding: '1em 0' }}>
            <p style={{ margin: '0 1em 0 0' }}>Include transfers?</p>
            <input
              name="includeTransfers"
              type="checkbox"
              checked={this.state.includeTransfers}
              onChange={evt =>
                this.handleToggle(evt, this.state.includeTransfers)
              }
            />
          </div>
          <AsyncButton
            onClick={() => this.attemptNewExport()}
            isLoading={this.props.newExportRequest.isRequesting}
            buttonStyle={{ display: 'flex' }}
            buttonText="Export"
          />
          <ErrorMessage>{this.props.newExportRequest.error}</ErrorMessage>
          <a
            href={this.props.newExportRequest.file_url}
            target="_blank"
            style={{
              display:
                this.props.newExportRequest.file_url === null ? 'none' : '',
            }}>
            Didn't automatically download?
          </a>
        </div>
      </div>
    );
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(ExportManager);

const SubRow = styled.div`
  display: flex;
  align-items: center;
  width: 33%;
  @media (max-width: 767px) {
    width: 100%;
    justify-content: space-between;
  }
`;

const ManagerInput = styled.input`
  color: #555;
  border: solid #d8dbdd;
  border-width: 0 0 1px 0;
  outline: none;
  margin-left: 0.5em;
  width: 50%;
  font-size: 15px;
  &:focus {
    border-color: #2d9ea0;
  }
`;

const InputLabel = styled.p`
  font-size: 15px;
`;

const Code = styled.p`
  text-align: center;
  font-size: 3em;
  font-weight: 700;
`;
