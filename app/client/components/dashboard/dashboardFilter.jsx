import React from 'react'
import { DateRangePicker } from 'react-dates'
import { loadCreditTransferStats } from "../../reducers/creditTransferReducer"
import { connect } from 'react-redux';
import styled from 'styled-components';
import { ModuleBox } from '../styledElements'
import SearchBoxWithFilter from '../SearchBoxWithFilter'

const mapStateToProps = (state) => {
    return {
        mergedTransferAccountUserList: Object.keys(state.transferAccounts.byId)
      .map((id) => {return {...{id, ...state.users.byId[state.transferAccounts.byId[id].primary_user_id]}, ...state.transferAccounts.byId[id]}})
      .filter(mergedObj => mergedObj.users && mergedObj.users.length >= 1),
    }
}

const mapDispatchToProps = (dispatch) => {
    return {
      loadCreditTransferStats: (query, path) => dispatch(loadCreditTransferStats({query, path}))
    };
  };

class DashboardFilter extends React.Component {
    constructor(props) {
        super(props);
        this.state = {
            filterActive: false,
            startDate: null,
            endDate: null,
            filters: []
        }
        this.searchKeys = [
            'balance',
            'created',
            'first_name',
            'last_name',
            'id',
            'is_approved',
            'phone',
            'public_serial_number'
          ];
      
        this.filterKeys = {
        'balance': amount => amount/100,
        'created': null,
        'is_approved': null,
        'location': null
        }
    }

    onDatesChange = ({startDate, endDate}) => {
        this.setState({
            startDate,
            endDate
        }, () => this.updateStats())
    }

    toggleFilter = () => {
        this.setState({filterActive: !this.state.filterActive})
    }

    onFiltersChanged = (filters) => {
        this.setState({
            filters: filters
        }, () => this.updateStats())
    }

    updateStats = () => {
        let {startDate, endDate, filters} = this.state
        console.log(filters)
        if(startDate && endDate) {
            this.props.loadCreditTransferStats({
              start_date: startDate.toISOString(),
              end_date: endDate.toISOString(),
              filters: btoa(JSON.stringify(filters))
            })
        } else {
            this.props.loadCreditTransferStats({
                filters: btoa(JSON.stringify(filters))
            })
        }
    }

    render() {
        var item_list = this.props.mergedTransferAccountUserList.sort((a, b) => (b.id - a.id));
        return (
            <div>
                <ModuleBox>
                    <DateRangePicker
                        isOutsideRange={() => false}
                        startDatePlaceholderText={"Start Date"}
                        endDatePlaceholderText={"End Date"}
                        withPortal={true}
                        startDate={this.state.startDate} // momentPropTypes.momentObj or null,
                        startDateId="your_unique_start_date_id" // PropTypes.string.isRequired,
                        endDate={this.state.endDate} // momentPropTypes.momentObj or null,
                        endDateId="your_unique_end_date_id" // PropTypes.string.isRequired,
                        onDatesChange={this.onDatesChange} // PropTypes.func.isRequired,
                        focusedInput={this.state.focusedInput} // PropTypes.oneOf([START_DATE, END_DATE]) or null,
                        onFocusChange={focusedInput => this.setState({ focusedInput })} // PropTypes.func.isRequired,
                    />
                </ModuleBox>
                <SearchBoxWithFilter
                    toggleTitle={"Account Filters"}
                    withSearch={false}
                    item_list={item_list}
                    onFiltersChanged={this.onFiltersChanged}
                    searchKeys={this.searchKeys}
                    filterKeys={this.filterKeys}>
                    <div>{this.props.children}</div>
                </SearchBoxWithFilter>
                
            </div>
            
        )
    }
}

export default connect(mapStateToProps, mapDispatchToProps)(DashboardFilter);