import React from "react";
import { StyledSelect, Input, StyledButton} from "./styledElements";
import styled from "styled-components";
import PropTypes from 'prop-types';
import { replaceUnderscores } from "../utils";

import {USER_FILTER_FIELD, USER_FILTER_TYPE} from '../constants';

const propTypes = {
    possibleFilters: PropTypes.object,
    onFiltersChanged: PropTypes.func,
    visible: PropTypes.bool
}
  
const defaultProps = {
    possibleFilters: [],
    onFiltersChanged: () => {
        console.log("Filters changed")
    },
    visible: true
}

class Filter extends React.Component {

    constructor() {
        super()
        this.state = {
            phrase: '',
            filters: [],
            keyName: 'select',
            value: 'select',
            filterType: 'of',
            comparator: '<',
            keyNameValues: {},
            possibleFilters: null,
            filterActive: false,
            dropdownActive: false,
            saveFilterDropdown: false,
            loadFiltersDropdown: false,
            filterName: null
        };
    }

    keyNameChange = (name, value) => {
        var keyNameProperties = this.props.possibleFilters[value]
        var keyNameValues = keyNameProperties.values;
          // resets keyName and keyNameValues to default to avoid controlled/uncontrolled checkbox error
          // maps over new keyNameValues,
        
        if (keyNameProperties.type === USER_FILTER_TYPE.DATE_RANGE){
            this.setState(
                {
                    [name]: value,
                    keyNameValues: {},
                    filterType: USER_FILTER_TYPE.DATE_RANGE,
                    GtLtThreshold: 0,
                    dropdownActive: false
                }
            );
        } else if (keyNameProperties.type === USER_FILTER_TYPE.INT_RANGE) {
            this.setState(
                {
                    [name]: value,
                    keyNameValues: {},
                    filterType: USER_FILTER_TYPE.DATE_RANGE,
                    GtLtThreshold: 0,
                    dropdownActive: false
                }
            );
        } else {
            this.setState(
                {
                    [name]: value,
                    keyNameValues: {},
                    filterType: USER_FILTER_TYPE.DISCRETE,
                    GtLtThreshold: 0,
                    dropdownActive: false
                }, () => {
                keyNameValues.map(i => {
                    this.setState(prevState => ({
                    keyNameValues: {
                        ...prevState.keyNameValues,
                        [i]: false
                    }
                    }))
                })
            });
        }
    }

    toggleSelected = (key) => {
        const value = !this.state.keyNameValues[key];
    
        this.setState(prevState => ({
          keyNameValues: {
            ...prevState.keyNameValues,
            [key]: value
          },
        }))
    }

    addFilter = () => {
        let id = this.state.filters.length + 1;
    
        if (this.state.filterType === USER_FILTER_TYPE.DISCRETE) {
            let values = this.get_selected_ids_array(this.state.keyNameValues)
            var newFilter = {
                'id': id,
                'type': USER_FILTER_TYPE.DISCRETE,
                'keyName': this.state.keyName,
                'allowedValues': values
            }
        } else {
            newFilter = {
                'id': id,
                'type': this.state.comparator,
                'keyName': this.state.keyName,
                'threshold': parseFloat(this.state.GtLtThreshold)
            }
        }
    
        this.setState(
          {filters: [...this.state.filters, newFilter]},
          () => {
            this.setState({
              keyName: 'select', value: 'select', keyNameValues: {}, filterType: 'of', GtLtThreshold: 0, dropdownActive: false
            })
            this.props.onFiltersChanged(this.state.filters)
          }
        )
    }

    removeFilter = (evt) => {
        let newFilters = [...this.state.filters].filter(filter => (filter.id !== parseInt(evt.target.name)));
        this.setState({filters: newFilters}, () => this.props.onFiltersChanged(this.state.filters))
    }
    

    attributePicker = () => {
        let {possibleFilters} = this.props
        let {keyName} = this.state
        const keys = (possibleFilters !== undefined && possibleFilters !== null ? Object.keys(possibleFilters).filter(key => (key !== 'profile_picture')) : []);

        return (
            <div style={{margin: '1em', display: 'flex', flexDirection: 'row', alignItems: 'center', flexFlow: 'row wrap'}}>

                <div style={{display: 'flex', flexDirection: 'row', alignItems: 'center'}}>
                    <FilterText style={{padding: '0 10px 0 0'}}>Filter:</FilterText>
                    <StyledSelectKey name="keyName" value={keyName} onChange={(evt) => this.keyNameChange(evt.target.name, evt.target.value)}>
                    <option name="key" value="select" disabled>select attribute</option>
                    {typeof(keys) !== 'undefined' ? keys.map((key, index) =>
                        <option name='value' value={key} key={index}>{replaceUnderscores(key)}</option>
                    ) : null}
                    </StyledSelectKey>
                </div>

            </div>
        )
    }

    comparatorChange(value) {
        console.log(value)
        this.setState({comparator: value})
    }

    get_selected_ids_array = (selected) => {
        Object.filter = (obj, predicate) => Object.keys(obj)
          .filter( key => predicate(obj[key]) ).reduce( (res, key) => (res[key] = obj[key], res), {} );
    
        return Object.keys(Object.filter(selected, selected => selected === true));
    }

    filterTypePicker = () => {
        let { filterType, keyName, comparator } = this.state
        var filter_type_picker = <div />;

        if (keyName !== 'select'){
            if (filterType === USER_FILTER_TYPE.DISCRETE) {
                filter_type_picker = <FilterText style={{padding: '0 10px'}}>is one of</FilterText>
            } else {
                filter_type_picker = (
                    <StyledSelectKey name="keyName" value={comparator} onChange={(evt) => this.comparatorChange(evt.target.value)}>
                    <option name='value' value={"<"}>is less than</option>
                    <option name='value' value={">"}>is greater than</option>
                    </StyledSelectKey>
                )
            }
        }
        return filter_type_picker
    }


    valuePicker = () => {
        let { possibleFilters } = this.props
        let { keyName, filterType, dropdownActive, value, keyNameValues } = this.state
        var valuePicker = <div/>;
        if (keyName !== 'select' && filterType === USER_FILTER_TYPE.DISCRETE) {
            valuePicker =
              <div style={{display: 'flex', flexDirection: 'row', alignItems: 'center'}}>
                <div style={{width: '200px'}}>
                  <div style={{width: 'inherit', position: 'relative'}} onClick={this.dropdownActive}>
                    <StyledSelectKey style={{width: 'inherit'}} name="value" value={value} onClick={this.dropdownActive} onChange={this.handleChange}>
                      <option name="value" value="select" disabled>select value</option>
                    </StyledSelectKey>
                    <div style={{position: 'absolute', top: 0, right: 0, bottom: 0, left: 0}}/>
                  </div>
                  <Checkboxes
                    style={{display: (dropdownActive ? 'block' : 'none')}}
                    onMouseLeave={() => this.setState({dropdownActive: !this.state.dropdownActive})}>
                    {typeof(possibleFilters[keyName].values) !== 'undefined' ? possibleFilters[keyName].values.map((key, index) => (
                        <CheckboxLabel key={index}>
                          <input type="checkbox" value={key} checked={keyNameValues[key]} onChange={() => this.toggleSelected(key)}/>
                          {replaceUnderscores(key)}
                        </CheckboxLabel>
                      )) : null}
                  </Checkboxes>
                  <CloseWrapper
                  onClick={() => this.setState({dropdownActive: !this.state.dropdownActive})}
                  style={{display: (this.state.dropdownActive ? '' : 'none')}}/>
                </div>
      
                {this.addFilterBtn()}
              </div>
        } else if (keyName !== 'select') {
            valuePicker =
              <div style={{display: 'flex', flexDirection: 'row', alignItems: 'center'}}>
                <ThresholdInput type="number" name="GtLtThreshold" value={this.state.GtLtThreshold} onChange={this.handleChange}/>
                {this.addFilterBtn()}
              </div>
        }
        return valuePicker;
    }

    dropdownActive = () => {
        this.setState({dropdownActive: !this.state.dropdownActive})
    }

    handleChange = (evt) => {
        console.log(evt)
        this.setState({ [evt.target.name]: evt.target.value });
    }

    addFilterBtn = () => {
        let {keyNameValues, filterType} = this.state
        let rowValues = Object.values(keyNameValues);
        let numberSelected = rowValues.filter(Boolean).length;
        let isSelected = numberSelected > 0 || filterType !== 'of';
        var addFilterBtn = <div/>
        if (isSelected) {
            addFilterBtn =
              <div>
                <StyledButton style={{fontWeight: '400', margin: '0em 1em', lineHeight: '25px', height: '25px'}} onClick={this.addFilter}>Add</StyledButton>
              </div>
        } 
        return addFilterBtn
    }

    activeFilterBubbles = () => {
        let {filters} = this.state
        let addedFilters = <div/>
        if (filters) {
            addedFilters =
              <div style={{display: 'flex', flexDirection: 'row', alignItems: 'center', margin: '0 1em', flexFlow: 'row wrap'}}>
                {filters.map((filter, index) => {
                  if (filter.type === USER_FILTER_TYPE.DISCRETE) {
                    return (
                      <FilterBubble key={index}>
                        <FilterText style={{color: '#FFF'}}>
                          {filter.keyName}: {filter.allowedValues.map((value, index) => {
                            if (filter.allowedValues.length === index+1) {
                              return value
                            } else {
                              return value + ' or '
                            }
                          })}
                        </FilterText>
                        <SVG name={filter.id} onClick={this.removeFilter} src="/static/media/close.svg"/>
                      </FilterBubble>
                    )
                  } else {
                    return (
                      <FilterBubble key={index}>
                        <FilterText style={{color: '#FFF'}}>
                          {filter.keyName} {filter.type} {filter.threshold}
                        </FilterText>
                        <SVG name={filter.id} onClick={this.removeFilter} src="/static/media/close.svg"/>
                      </FilterBubble>
                    )
                  }
                })}
              </div>
        }
        return addedFilters
    }

    render() {

        return (
            <div style={{display: 'flex', flexDirection: 'column'}}>
                {this.activeFilterBubbles()}
                <div style={{display: 'flex', flexDirection: 'row', alignItems: 'center', flexFlow: 'row wrap'}}>
                    {this.attributePicker()}
                    {this.filterTypePicker()}
                    {this.valuePicker()}
                </div>
            </div>
        )
    }


}

Filter.defaultProps = defaultProps,
Filter.propTypes = propTypes

export default Filter;


const FilterText = styled.p`
  margin: 0;
  font: 400 11px system-ui;
  color: #777;
  padding: 0 0 0 10px;
`;

const StyledSelectKey = styled(StyledSelect)`
  box-shadow: 0 0 0 1px rgba(44,45,48,.15);
  font: 400 12px system-ui;
  color: #777;
  padding: 0 0 0 10px;
  margin: 5px;
  line-height: 25px;
  height: 25px;
  
`;

const ThresholdInput = styled(Input)`
  font: 400 12px system-ui;
  border-radius: 5px;
  height: 12px;
`;

const FilterBubble = styled.div`
  display: flex;
  align-items: center;
  width: fit-content;
  margin: 10px 10px 0 0;
  font: 400 12px system-ui;
  color: #fff;
  padding: 5px 0;
  background-color: #607D8B;
  border-radius: 10px;
`;

const SVG = styled.img`
  width: 12px;
  padding: 0px 10px;
`;

const Checkboxes = styled.div`
  display: block;
  position: absolute;
  z-index: 55;
  background-color: rgb(255, 255, 255);
  width: inherit;
  border-radius: 2px;
  margin: 5px;
  box-shadow: 0 0 0 1px rgba(44,45,48,.15), 0 5px 10px rgba(44,45,48,.12);
`;

const CheckboxLabel = styled.label`
  border-bottom: 1px solid #eaedef;
  padding: 5px;
  font: 400 12px system-ui;
  color: #777;
  display: block;
  &:hover {
  background-color: #f7fafc;
  }
  &::selection {
  background: none;
  }
  &:last-child {
  border-bottom: none;
  }
`;

const CloseWrapper = styled.div`
	position: fixed;
	top: 0;
	left: 0;
	background-color: transparent;
	z-index: 54;
	width: 100vw;
	height: 100vh;
`;