import React from "react";
import { connect } from 'react-redux';
import { ModuleBox, StyledSelect, Input} from "./styledElements";
import styled from "styled-components";
import matchSorter from "match-sorter";

import { replaceUnderscores } from "../utils";
import {loadFilters, createFilter} from "../reducers/filterReducer";
import LoadingSpinner from "./loadingSpinner.jsx";

const mapStateToProps = (state) => {
  return {
  	filters: state.filters,
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    loadFilters: () => dispatch(loadFilters()),
    createFilter: (body) => dispatch(createFilter({body}))
  };
};

class SearchBoxWithFilter extends React.Component {
  constructor()
  {
    super();
    this.state = {
      phrase: '',
      filters: [],
      keyName: 'select',
      value: 'select',
      filterType: 'of',
      keyNameValues: {},
      possibleFilters: null,
      filterActive: false,
      dropdownActive: false,
      saveFilterDropdown: false,
      loadFiltersDropdown: false,
      filterName: null,
      attributeListIsFullyFloatParsable: false,
      GtLtThreshold: 0
    };
    this.keyNameChange = this.keyNameChange.bind(this);
    this.handleChange = this.handleChange.bind(this);
    this.addFilter = this.addFilter.bind(this);
    this.removeFilter = this.removeFilter.bind(this);
    this.toggleFilter = this.toggleFilter.bind(this);
    this.dropdownActive = this.dropdownActive.bind(this);
    this.saveFilter = this.saveFilter.bind(this);
    this.saveFilterDropdown = this.saveFilterDropdown.bind(this);
    this.loadFilters = this.loadFilters.bind(this);
    this.loadSavedFilter = this.loadSavedFilter.bind(this);
  }

  componentDidMount() {
    let custom_attribute_dict = this.getPossibleFilters();
    this.setState({ possibleFilters: custom_attribute_dict })
  }

  componentDidUpdate(newProps) {
    if (this.props.item_list !== newProps.item_list) {
      let custom_attribute_dict = this.getPossibleFilters();
      this.setState({ possibleFilters: custom_attribute_dict })
    }
  }

  saveFilter() {
    this.props.createFilter({
      filter_name: this.state.filterName,
      filter_attributes: this.state.filters
    })
  }

  loadFilters() {
    if (!this.state.loadFiltersDropdown) {
      // load filters hasn't been clicked
      this.props.loadFilters()
    }
    // toggle dropdown
    this.setState({loadFiltersDropdown: !this.state.loadFiltersDropdown});
  }

  loadSavedFilter(filterId) {
    const savedFilter = this.props.filters.byId[filterId];
    this.setState({filters: savedFilter.filter, filterName: savedFilter.name});
  }

  getPossibleFilters() {
    var attribute_dict = {};
    var item_list = this.props.item_list;

    const proccess_attribute = (name, value) => {
      if (attribute_dict[name] === undefined) {
        // This means that the attribute name has not been seen at all, which means we can just create array
        attribute_dict[name] = [value]
      } else {
        // Attribute name has been seen, check if attribute VALUE has been seen
        if (attribute_dict[name].indexOf(value) === -1) {
          //hasn't been seen, so add
          attribute_dict[name].push(value)
        }
      }
    };

    if (item_list !== undefined) {
      // get attributes names and possible values
      item_list
        .filter(item => item.custom_attributes !== undefined)
        .map(item => Object.keys(item.custom_attributes).map(attribute_name => {
          let attribute_value = item.custom_attributes[attribute_name]['value'];
          proccess_attribute(attribute_name, attribute_value)
        }));

      item_list.map(item => {
        Object.keys(this.props.filterKeys).map( key => {
          let attribute_value = item[key];
          if (this.props.filterKeys[key] !== null) {
            proccess_attribute(key, this.props.filterKeys[key](attribute_value))
          } else {
            proccess_attribute(key, attribute_value)
          }
        })
      })
    }

    return attribute_dict
  }

  keyNameChange(name, value) {
    var keyNameValues = this.state.possibleFilters[value];
    // this.setState({ [evt.target.name]: evt.target.value });
    if (keyNameValues !== undefined) {
      // resets keyName and keyNameValues to default to avoid controlled/uncontrolled checkbox error
      // maps over new keyNameValues,

      this.setState(
        {
          [name]: 'select',
          keyNameValues: {},
          filterType: 'of',
          GtLtThreshold: 0,
          dropdownActive: false
        }, () => {
        let attributeListIsFullyFloatParsable = true;
        keyNameValues.map(i => {
          if (isNaN(parseFloat(i))) {attributeListIsFullyFloatParsable = false}
          this.setState(prevState => ({
            [name]: value,
            keyNameValues: {
              ...prevState.keyNameValues,
              [i]: false
            }
          }))
        })
        this.setState({attributeListIsFullyFloatParsable})
      });
    }
  }

  filterTypeChange(name, value) {
    this.setState({filterType: value})
  }

  handleChange(evt) {
    this.setState({ [evt.target.name]: evt.target.value });
  }

  addFilter() {
    let id = this.state.filters.length + 1;

    if (this.state.filterType === 'of') {
      var newFilter = {
        'id': id,
        'type': 'of',
        'keyName': this.state.keyName,
        'allowedValues': this.get_selected_ids_array(this.state.keyNameValues)
      }
    } else {
      newFilter = {
        'id': id,
        'type': this.state.filterType,
        'keyName': this.state.keyName,
        'threshold': parseFloat(this.state.GtLtThreshold)
      }
    }

    this.setState(
      {filters: [...this.state.filters, newFilter]},
      () => this.setState({
        keyName: 'select', value: 'select', keyNameValues: {}, filterType: 'of', GtLtThreshold: 0, dropdownActive: false
      })
    )
  }

  removeFilter(evt) {
    let newFilters = [...this.state.filters].filter(filter => (filter.id !== parseInt(evt.target.name)));
    this.setState({filters: newFilters})
  }

  toggleSelected(key) {
    const value = !this.state.keyNameValues[key];

    this.setState(prevState => ({
      keyNameValues: {
        ...prevState.keyNameValues,
        [key]: value
      },
    }))
  }

  toggleFilter() {
    this.setState({filterActive: !this.state.filterActive})
  }

  dropdownActive() {
    this.setState({dropdownActive: !this.state.dropdownActive})
  }

  saveFilterDropdown() {
    this.setState({saveFilterDropdown: !this.state.saveFilterDropdown})
  }

  applyFilter(item_list, filter) {
    return item_list.reduce((filtered, item) => {

      let added = false;

      const add_account = () => {
        filtered.push(item);
        added = true;
      };

      const test_conditions = (filter,value) => {
        if (filter.type === 'of') {
          if (filter.allowedValues.includes((value || '').toString())) {
            // attribute value is in allowed value, add account to filtered
            add_account()
          }
        } else if (filter.type === '<') {
          if (value < filter.threshold) {
            add_account()
          }
        } else if (filter.type === '>') {
          if (value > filter.threshold) {
            add_account()
          }
        }
      };

      //Filtering Standard Attributes
      Object.keys(item).map(attribute_name => {

        let key = filter.keyName;
        if (attribute_name === key) {
          // attribute name matches key name, apply filter test
          var attribute_value = item[attribute_name];
          if (this.props.filterKeys[key] !== null) {
            attribute_value = this.props.filterKeys[key](attribute_value)
          }

          test_conditions(filter, attribute_value)
        }

      });

      if (added === false && item.custom_attributes !== undefined) {
        //Filtering Custom Attributes
        Object.keys(item.custom_attributes).map(attribute_name => {
          if (attribute_name === filter.keyName) {
           let attribute_value = item.custom_attributes[attribute_name].value;
           test_conditions(filter, attribute_value)
          }
        })
      }

      return filtered;
    }, []);
  }

  get_selected_ids_array(selected) {
    Object.filter = (obj, predicate) => Object.keys(obj)
      .filter( key => predicate(obj[key]) ).reduce( (res, key) => (res[key] = obj[key], res), {} );

    return Object.keys(Object.filter(selected, selected => selected === true));
  }

  render() {
    const {
      phrase, filters, keyName, value,
      filterType, filterActive, possibleFilters,
      keyNameValues, attributeListIsFullyFloatParsable, saveFilterDropdown
    } = this.state;

    var item_list = this.props.item_list;

    let rowValues = Object.values(keyNameValues);
    let numberSelected = rowValues.filter(Boolean).length;
    let isSelected = numberSelected > 0 || filterType !== 'of';

    // get possible filter keys, remove PROFILE_PICTURE
    const keys = (possibleFilters !== undefined && possibleFilters !== null ? Object.keys(possibleFilters).filter(key => (key !== 'profile_picture')) : []);

    let creditTransferSearchKeys = ['transfer_amount', 'created', 'transfer_status', 'transfer_type', 'id', 'transfer_use', 'recipient', 'sender'];
    let transferAccountSearchKeys = ['balance', 'created', 'first_name', 'last_name', 'id', 'location', 'is_approved', 'phone', 'nfc_serial_number', 'public_serial_number'];

    // pass correct keys to search filter
    let searchKeys = location.pathname.includes('transfers') ? creditTransferSearchKeys : location.pathname.includes('accounts') ? transferAccountSearchKeys : [];

    // Phrase Search
    if (phrase !== '') {
      item_list = matchSorter(item_list, this.state.phrase, {keys: this.props.searchKeys});
    }

    if (filters.length > 0 && item_list.length > 0) {
      this.state.filters.map(filter => {
        item_list = this.applyFilter(item_list, filter)
      });
    }

    if (isSelected) {
      var addFilterBtn =
        <div>
          <FilterText onClick={this.addFilter}>Add</FilterText>
        </div>
    }




    if (keyName !== 'select')
    {
      if (!attributeListIsFullyFloatParsable) {
        var filter_type_picker = <FilterText style={{padding: '0 10px'}}>is one of</FilterText>
      } else {
        filter_type_picker = (
          <StyledSelectKey name="keyName" value={filterType} onChange={(evt) => this.filterTypeChange(evt.target.name, evt.target.value)}>
            <option name='value' value={"<"}>is less than</option>
            <option name='value' value={"of"}>is one of</option>
            <option name='value' value={">"}>is greater than</option>
          </StyledSelectKey>
        )
      }
    }

    if (keyName !== 'select' && filterType === 'of') {

      var valuePicker =
        <div style={{display: 'flex', flexDirection: 'row', alignItems: 'center'}}>
          <div style={{width: '200px'}}>
            <div style={{width: 'inherit', position: 'relative'}} onClick={this.dropdownActive}>
              <StyledSelectKey style={{width: 'inherit'}} name="value" value={value} onClick={this.dropdownActive} onChange={this.handleChange}>
                <option name="value" value="select" disabled>select value</option>
                {/*{typeof(custom_attribute_dict[keyName]) !== 'undefined' ? custom_attribute_dict[keyName].map((key, index) => {return (<option name='value' value={key} key={index}>{key}</option>)}) : null}*/}
              </StyledSelectKey>
              <div style={{position: 'absolute', top: 0, right: 0, bottom: 0, left: 0}}/>
            </div>
            <Checkboxes
              style={{display: (this.state.dropdownActive ? 'block' : 'none')}}
              onMouseLeave={() => this.setState({dropdownActive: !this.state.dropdownActive})}>
              {typeof(possibleFilters[keyName]) !== 'undefined' ? possibleFilters[keyName].map((key, index) => (
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

          {addFilterBtn}
        </div>
    } else if (keyName !== 'select') {
      valuePicker =
        <div style={{display: 'flex', flexDirection: 'row', alignItems: 'center'}}>
          <ThresholdInput type="number" name="GtLtThreshold" value={this.state.GtLtThreshold} onChange={this.handleChange}/>
          {addFilterBtn}
        </div>
    }

    if (filterActive) {
      var newFilterSection =
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
          {filter_type_picker}
          {valuePicker}

        </div>
    } else {
      newFilterSection = null;
    }

    if (filters) {
      var addedFilters =
        <div style={{display: 'flex', flexDirection: 'row', alignItems: 'center', margin: '0 1em', flexFlow: 'row wrap'}}>
          {filters.map((filter, index) => {
            if (filter.type === 'of') {
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

    if (this.props.filters.loadStatus.isRequesting) {
      var filterList =
        <div style={{padding: '1em'}}>
          <LoadingSpinner/>
        </div>
    } else if (this.props.filters.loadStatus.success) {
      let filterListKeys = Object.keys(this.props.filters.byId).filter(id => typeof(this.props.filters.byId[id]) !== "undefined").map(id => this.props.filters.byId[id]);
      filterList = filterListKeys.map((filter, index) => {return (<CheckboxLabel name={filter.id} key={index} onClick={() => this.loadSavedFilter(filter.id)}>{filter.name}</CheckboxLabel>)});
    } else {
      filterList = null
    }

    if (filterActive && filters.length !== 0) {
      var savedFilters =
        <div style={{margin: '0 1em', position: 'relative'}}>
          <ModuleBox style={{margin: 0, padding: 0, fontSize: '0.8em', width: 'fit-content'}} onClick={this.saveFilterDropdown}>
            <SavedFilterButton>{saveFilterDropdown ? null : <SVG style={{padding: '0 5px 0 0'}} src="/static/media/save.svg"/>}{saveFilterDropdown ? 'Cancel' : 'Save Filter'}</SavedFilterButton>
          </ModuleBox>
          <SavedFilters style={{display: (this.state.saveFilterDropdown ? 'block' : 'none')}}>
            <ThresholdInput name="filterName" value={this.state.filterName} placeholder='Filter name...' onChange={this.handleChange}/>
            <FilterText onClick={this.saveFilter} style={{padding: '0 0 5px 10px'}}>Save Filter</FilterText>
          </SavedFilters>
        </div>
    } else if (filterActive) {
      savedFilters =
        <div style={{margin: '0 1em', display: 'flex', position: 'relative'}}>
          <ModuleBox style={{margin: 0, padding: 0, fontSize: '0.8em'}} onClick={this.loadFilters}>
            <SavedFilterButton>
              <SVG style={{padding: '0 5px 0 0'}} src="/static/media/save.svg"/>
              View Saved Filters
            </SavedFilterButton>
          </ModuleBox>
          <SavedFilters style={{display: (this.state.loadFiltersDropdown ? 'block' : 'none')}}>
            {filterList}
          </SavedFilters>
          <CloseWrapper
			  onClick={() => this.setState({loadFiltersDropdown: !this.state.loadFiltersDropdown})}
			  style={{display: (this.state.loadFiltersDropdown ? '' : 'none')}}/>
        </div>
    }

    return(


      <div>
        <ModuleBox>
          <SearchWrapper>
            <svg style={{ width: 18, height: 18, paddingTop: 10, paddingRight: 10, paddingBottom: 10, paddingLeft: 10 }}
                 height='16' viewBox='0 0 16 16' width='16' xmlns='http://www.w3.org/2000/svg'>
              <path d='M12.6 11.2c.037.028.073.059.107.093l3 3a1 1 0 1 1-1.414 1.414l-3-3a1.009 1.009 0 0 1-.093-.107 7 7 0 1 1 1.4-1.4zM7 12A5 5 0 1 0 7 2a5 5 0 0 0 0 10z' fillRule='evenodd' fill='#6a7680' />
            </svg>
            <SearchInput name="phrase" value={phrase} placeholder="Search..." onChange={this.handleChange} />

            <FilterWrapper onClick={this.toggleFilter}>
              <FilterText>{filterActive ? 'Cancel' : 'Filters'}</FilterText>
              <svg style={{ width: 12, height: 12, padding: '0 10px', transform: filterActive ? 'rotate(45deg)' : null, transition: 'all .15s ease' }} height='16' viewBox='0 0 16 16' width='16' xmlns='http://www.w3.org/2000/svg'>
                <path d='M9 7h6a1 1 0 0 1 0 2H9v6a1 1 0 0 1-2 0V9H1a1 1 0 1 1 0-2h6V1a1 1 0 1 1 2 0z'
                fillRule='evenodd' fill='#6a7680' />
              </svg>
            </FilterWrapper>

          </SearchWrapper>
        </ModuleBox>

        {savedFilters}
        {addedFilters}
        {newFilterSection}

        <div>{React.cloneElement(this.props.children, { item_list: item_list })}</div>
      </div>
    )
  }
}

export default connect(mapStateToProps, mapDispatchToProps)(SearchBoxWithFilter);

const SearchWrapper = styled.div`
  display: flex;
  flex-direction: row;
  justify-content: center;
  align-items: center;
`;

const SearchInput = styled.input`
  margin: 2px 0 0 -40px;
  border: solid #FFF;
  border-width: 0 0 2px 0;
  padding: 1em 1em 1em 40px;
  width: 100%;
  outline: none;
  background: transparent;
  &:focus {
  border-color: #2D9EA0;
  }
`;

const FilterText = styled.p`
  margin: 0;
  font: 400 11px system-ui;
  color: #777;
  padding: 0 0 0 10px;
`;

const FilterWrapper = styled.div`
  display: flex;
  flex-direction: row;
  height: 39px;
  align-items: center;
  border-left: solid 1px #e8e8ea;
  &:hover {
  background-color: #f7fafc;
  }
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

const SavedFilterButton = styled.div`
  align-items: center;
  display: flex;
  margin: 0;
  font: 400 12px system-ui;
  color: #777;
  padding: 0.6em;
  &:hover {
  background-color: #f7fafc;
  }
`;

const SavedFilters = styled.div`
    display: block;
    border-radius: 2px;
    margin-top: 10px;
    position: absolute;
    top: 29px;
    width: 200px;
    z-index: 55;
    background-color: rgb(255,255,255);
    width: inherit;
    /* border-radius: 2px; */
    box-shadow: 0 0 0 1px rgba(44,45,48,.15), 0 5px 10px rgba(44,45,48,.12);
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
