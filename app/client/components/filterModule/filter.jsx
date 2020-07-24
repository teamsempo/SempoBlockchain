import React from "react";
import { Select } from "antd";
const { Option, OptGroup } = Select;

import { StyledSelect, Input, StyledButton } from "../styledElements.js";
import styled from "styled-components";
import PropTypes from "prop-types";
import { replaceUnderscores } from "../../utils.js";
import { SingleDatePicker } from "react-dates";

import moment from "moment";

import { USER_FILTER_TYPE, USER_FILTER_ATTRIBUTE } from "../../constants.js";

const propTypes = {
  possibleFilters: PropTypes.object,
  onFiltersChanged: PropTypes.func,
  visible: PropTypes.bool,
  label: PropTypes.string
};

const defaultProps = {
  possibleFilters: [],
  onFiltersChanged: () => {
    console.log("Filters changed");
  },
  visible: true,
  label: "Filter:"
};

class Filter extends React.Component {
  constructor() {
    super();

    this.state = {
      phrase: "",
      date: moment(),
      focused: false,
      filters: [],
      attribute: "select",
      filterType: "of",
      comparator: "<",
      attributeValues: {},
      discreteOptions: [],
      discreteSelected: [],
      possibleFilters: null,
      filterActive: false,
      dropdownActive: false,
      saveFilterDropdown: false,
      loadFiltersDropdown: false,
      filterName: null,
      selectorKeyBase: ""
    };
  }

  handleAttributeSelectorChange = attribute => {
    var attributeProperties = this.props.possibleFilters[attribute];

    if (attributeProperties.type === USER_FILTER_TYPE.DATE_RANGE) {
      this.setState({
        attribute: attribute,
        filterType: USER_FILTER_TYPE.DATE_RANGE,
        GtLtThreshold: 0,
        dropdownActive: false
      });
    } else if (attributeProperties.type === USER_FILTER_TYPE.INT_RANGE) {
      this.setState({
        attribute: attribute,
        filterType: USER_FILTER_TYPE.INT_RANGE,
        GtLtThreshold: 0,
        dropdownActive: false
      });
    } else {
      this.setState({
        attribute: attribute,
        filterType: USER_FILTER_TYPE.DISCRETE,
        GtLtThreshold: 0,
        discreteSelected: [],
        dropdownActive: false,
        discreteOptions: attributeProperties.values
      });
    }
  };

  attributePicker = () => {
    let { possibleFilters } = this.props;
    const keys =
      possibleFilters !== undefined && possibleFilters !== null
        ? Object.keys(possibleFilters).filter(key => key !== "profile_picture")
        : [];

    return (
      <div
        key={this.state.selectorKeyBase + "AS"}
        style={{
          margin: "1em",
          marginRight: "0em",
          display: "flex",
          flexDirection: "row",
          alignItems: "center",
          flexFlow: "row wrap"
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center"
          }}
        >
          <FilterText style={{ padding: "0 10px 0 0" }}>
            {this.props.label}
          </FilterText>

          <Select
            defaultValue="Select Attribute"
            onChange={this.handleAttributeSelectorChange}
          >
            {typeof keys !== "undefined"
              ? keys.map((key, index) => (
                  <Option key={key}>
                    {replaceUnderscores(possibleFilters[key]["name"] || key)}
                  </Option>
                ))
              : null}
          </Select>
        </div>
      </div>
    );
  };

  comparatorChange(value) {
    this.setState({ comparator: value });
  }

  get_selected_ids_array = selected => {
    Object.filter = (obj, predicate) =>
      Object.keys(obj)
        .filter(key => predicate(obj[key]))
        .reduce((res, key) => ((res[key] = obj[key]), res), {});

    return Object.keys(Object.filter(selected, selected => selected === true));
  };

  filterTypePicker = () => {
    let { filterType, attribute, comparator } = this.state;
    var filter_type_picker = <div />;

    if (attribute !== "select") {
      if (
        filterType === USER_FILTER_TYPE.DISCRETE ||
        USER_FILTER_TYPE.BOOLEAN_MAPPING === filterType
      ) {
        filter_type_picker = (
          <FilterText style={{ padding: "0 10px" }}>is one of</FilterText>
        );
      } else {
        filter_type_picker = (
          <StyledSelectKey
            name="keyName"
            value={comparator}
            onChange={evt => this.comparatorChange(evt.target.value)}
          >
            <option name="value" value={"<"}>
              {filterType === USER_FILTER_TYPE.DATE_RANGE
                ? "before"
                : "is less than"}
            </option>
            <option name="value" value={">"}>
              {filterType === USER_FILTER_TYPE.DATE_RANGE
                ? "after"
                : "is greater than"}
            </option>
          </StyledSelectKey>
        );
      }
    }
    return filter_type_picker;
  };

  handleDiscreteSelect = values => {
    this.setState({
      discreteSelected: values
    });
  };

  toggleSelected = key => {
    const value = !this.state.attributeValues[key];

    this.setState(prevState => ({
      attributeValues: {
        ...prevState.attributeValues,
        [key]: value
      }
    }));
  };

  valuePicker = () => {
    let { filterType, attribute } = this.state;

    if (attribute === "select") {
      return <div />;
    }

    if (
      filterType === USER_FILTER_TYPE.DISCRETE ||
      filterType === USER_FILTER_TYPE.BOOLEAN_MAPPING
    ) {
      return this.discreteValuePicker();
    }

    return this.dateValuePicker();
  };

  discreteValuePicker = () => {
    let { possibleFilters } = this.props;

    let { attribute } = this.state;

    let valueArray =
      typeof possibleFilters[attribute].values !== "undefined"
        ? [...possibleFilters[attribute].values]
        : [];

    return (
      <div
        style={{
          display: "flex",
          flexDirection: "row",
          alignItems: "center"
        }}
      >
        <Select
          mode="multiple"
          style={{ minWidth: "250px" }}
          placeholder="Please select"
          onChange={this.handleDiscreteSelect}
        >
          {valueArray.length !== 0
            ? valueArray.map(value => (
                <Option key={value}>{replaceUnderscores(value)}</Option>
              ))
            : null}
        </Select>
        {this.addFilterBtn()}
      </div>
    );
  };

  dateValuePicker = () => {
    let { filterType } = this.state;

    return (
      <div
        style={{
          display: "flex",
          flexDirection: "row",
          alignItems: "center"
        }}
      >
        {/* <ThresholdInput type="number" name="GtLtThreshold" value={this.state.GtLtThreshold} onChange={this.handleChange}/> */}
        {filterType === USER_FILTER_TYPE.DATE_RANGE ? (
          <StyledWrapper>
            <SingleDatePicker
              noBorder={false}
              small={true}
              isOutsideRange={() => false}
              date={this.state.date} // momentPropTypes.momentObj or null
              onDateChange={date => this.setState({ date: date })} // PropTypes.func.isRequired
              numberOfMonths={1}
              focused={this.state.focused} // PropTypes.bool
              onFocusChange={({ focused }) => this.setState({ focused })} // PropTypes.func.isRequired
              id="your_unique_id" // PropTypes.string.isRequired,
            />
          </StyledWrapper>
        ) : (
          <ThresholdInput
            type="number"
            name="GtLtThreshold"
            value={this.state.GtLtThreshold}
            onChange={this.handleChange}
          />
        )}
        {this.addFilterBtn()}
      </div>
    );
  };

  dropdownActive = () => {
    this.setState({ dropdownActive: !this.state.dropdownActive });
  };

  handleChange = evt => {
    this.setState({ [evt.target.name]: evt.target.value });
  };

  handleAddFilter = () => {
    let id = this.state.filters.length + 1;
    var newFilter;
    if (
      this.state.filterType === USER_FILTER_TYPE.DISCRETE ||
      USER_FILTER_TYPE.BOOLEAN_MAPPING == this.state.filterType
    ) {
      let values = this.get_selected_ids_array(this.state.attributeValues);
      newFilter = {
        id: id,
        type: USER_FILTER_TYPE.DISCRETE,
        attribute: this.state.attribute,
        allowedValues: this.state.discreteSelected
      };
    } else if (this.state.filterType === USER_FILTER_TYPE.DATE_RANGE) {
      newFilter = {
        id: id,
        type: this.state.comparator,
        attribute: this.state.attribute,
        threshold: this.state.date.format("YYYY-MM-DD")
      };
    } else {
      let value = parseFloat(this.state.GtLtThreshold);
      newFilter = {
        id: id,
        type: this.state.comparator,
        attribute: this.state.attribute,
        threshold: value
      };
    }

    this.setState({ filters: [...this.state.filters, newFilter] }, () => {
      this.setState({
        attribute: "select",
        value: "select",
        attributeValues: {},
        filterType: "of",
        GtLtThreshold: 0,
        dropdownActive: false,
        selectorKeyBase: `${Math.random()}`
      });
      this.props.onFiltersChanged(this.state.filters);
    });
  };

  removeFilter = evt => {
    let newFilters = [...this.state.filters].filter(
      filter => filter.id !== parseInt(evt.target.name)
    );
    this.setState({ filters: newFilters }, () =>
      this.props.onFiltersChanged(this.state.filters)
    );
  };

  addFilterBtn = () => {
    let { attributeValues, filterType } = this.state;
    let rowValues = Object.values(attributeValues);
    let numberSelected = rowValues.filter(Boolean).length;
    let isSelected = numberSelected > 0 || filterType !== "of";
    var addFilterBtn = <div />;
    if (isSelected) {
      addFilterBtn = (
        <div>
          <StyledButton
            style={{
              fontWeight: "400",
              margin: "0em 1em",
              lineHeight: "25px",
              height: "25px"
            }}
            onClick={this.handleAddFilter}
          >
            Add
          </StyledButton>
        </div>
      );
    }
    return addFilterBtn;
  };

  activeFilterBubbles = () => {
    let { filters } = this.state;
    let addedFilters = <div />;
    if (filters) {
      addedFilters = (
        <div
          style={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
            margin: "0 1em",
            flexFlow: "row wrap"
          }}
        >
          {filters.map((filter, index) => {
            if (
              filter.type === USER_FILTER_TYPE.DISCRETE ||
              filter.type === USER_FILTER_TYPE.BOOLEAN_MAPPING
            ) {
              return (
                <FilterBubble key={index}>
                  <FilterText style={{ color: "#FFF" }}>
                    {filter.attribute}:{" "}
                    {filter.allowedValues.map((value, index) => {
                      if (filter.allowedValues.length === index + 1) {
                        return value;
                      } else {
                        return value + " or ";
                      }
                    })}
                  </FilterText>
                  <SVG
                    name={filter.id}
                    onClick={this.removeFilter}
                    src="/static/media/close.svg"
                  />
                </FilterBubble>
              );
            } else {
              return (
                <FilterBubble key={index}>
                  <FilterText style={{ color: "#FFF" }}>
                    {filter.attribute} {filter.type} {filter.threshold}
                  </FilterText>
                  <SVG
                    name={filter.id}
                    onClick={this.removeFilter}
                    src="/static/media/close.svg"
                  />
                </FilterBubble>
              );
            }
          })}
        </div>
      );
    }
    return addedFilters;
  };

  render() {
    return (
      <div style={{ display: "flex", flexDirection: "column" }}>
        <div
          style={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
            flexFlow: "row wrap"
          }}
        >
          {this.attributePicker()}
          {this.filterTypePicker()}
          {this.valuePicker()}
        </div>
        {this.activeFilterBubbles()}
      </div>
    );
  }
}

(Filter.defaultProps = defaultProps), (Filter.propTypes = propTypes);

export default Filter;

const FilterText = styled.p`
  margin: 0;
  font: 400 11px system-ui;
  color: #777;
  padding: 0 0 0 10px;
`;

const StyledSelectKey = styled(StyledSelect)`
  box-shadow: 0 0 0 1px rgba(44, 45, 48, 0.15);
  font: 400 12px system-ui;
  color: #777;
  background-color: white;
  padding: 0 0 0 10px;
  margin: 5px;
  line-height: 25px;
  height: 25px;
  &:hover {
    background-color: white;
  }
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
  background-color: #607d8b;
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
  box-shadow: 0 0 0 1px rgba(44, 45, 48, 0.15),
    0 5px 10px rgba(44, 45, 48, 0.12);
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

const StyledWrapper = styled.div`
  .SingleDatePickerInput {
    border-radius: 5px;
  }
  .DateInput__small {
    border-radius: 5px;
  }
  .DateInput_input__small {
    height: 12px;
    border-radius: 5px;
    border-bottom: 2px solid white;
  }
  .DateInput_input__focused {
  }
`;
//
// <StyledSelectKey
//             name="keyName"
//             value={keyName}
//             onChange={evt =>
//               this.keyNameChange(evt.target.name, evt.target.value)
//             }
//           >
//             <option name="key" value="select" disabled>
//               select attribute
//             </option>
//             {typeof keys !== "undefined"
//               ? keys.map((key, index) => (
//                   <option
//                     name="value"
//                     value={key}
//                     key={index}
//                     style={{ color: "green" }}
//                   >
//                     {replaceUnderscores(possibleFilters[key]["name"] || key)}
//                   </option>
//                 ))
//               : null}
//           </StyledSelectKey>

//
// olddiscreteValuePicker = () => {
//
//     let { possibleFilters } = this.props;
//
//     let {
//       dropdownActive,
//       attribute,
//       attributeValues
//     } = this.state;
//
//     let valueArray =
//       typeof possibleFilters[attribute].values !== "undefined"
//         ? [...possibleFilters[attribute].values]
//         : [];
//
//     return (
//       <div
//         style={{
//           display: "flex",
//           flexDirection: "row",
//           alignItems: "center"
//         }}
//       >
//         <div style={{ width: "200px" }}>
//           <div
//             style={{ width: "inherit", position: "relative" }}
//             onClick={this.dropdownActive}
//           >
//             <StyledSelectKey
//               style={{ width: "inherit" }}
//               name="value"
//               value={attribute}
//               onClick={this.dropdownActive}
//               onChange={this.handleChange}
//             >
//               <option name="value" value="select" disabled>
//                 select value
//               </option>
//             </StyledSelectKey>
//             <div
//               style={{
//                 position: "absolute",
//                 top: 0,
//                 right: 0,
//                 bottom: 0,
//                 left: 0
//               }}
//             />
//           </div>
//           <Checkboxes
//             style={{ display: dropdownActive ? "block" : "none" }}
//             onMouseLeave={() =>
//               this.setState({ dropdownActive: !this.state.dropdownActive })
//             }
//           >
//             {valueArray.length !== 0
//               ? valueArray.map((key, index) => (
//                   <CheckboxLabel key={index}>
//                     <input
//                       type="checkbox"
//                       value={key}
//                       checked={attributeValues[key]}
//                       onChange={() => this.toggleSelected(key)}
//                     />
//                     {replaceUnderscores(key)}
//                   </CheckboxLabel>
//                 ))
//               : null}
//           </Checkboxes>
//           <CloseWrapper
//             onClick={() =>
//               this.setState({ dropdownActive: !this.state.dropdownActive })
//             }
//             style={{ display: this.state.dropdownActive ? "" : "none" }}
//           />
//         </div>
//
//         {this.addFilterBtn()}
//       </div>
//     );
//   };
