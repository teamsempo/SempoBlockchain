// Copyright (C) Sempo Pty Ltd, Inc - All Rights Reserved
// The code in this file is not included in the GPL license applied to this repository
// Unauthorized copying of this file, via any medium is strictly prohibited

import React from "react";
import { Select, InputNumber, DatePicker, Button } from "antd";
const { Option, OptGroup } = Select;

import { DefaultTheme } from "../theme";

import styled from "styled-components";
import PropTypes from "prop-types";
import { replaceUnderscores } from "../../utils.js";

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
      filters: [],
      selectorKeyBase: "",
      ...this.baseRuleConstructionState
    };
  }

  baseRuleConstructionState = {
    attribute: "select",
    filterType: "of",
    comparator: "=",
    discreteOptions: [],
    discreteSelected: [],
    GtLtThreshold: 0,
    date: moment()
  };

  handleAttributeSelectorChange = attribute => {
    let attributeProperties = this.props.possibleFilters[attribute];

    if (attributeProperties.type === USER_FILTER_TYPE.DATE_RANGE) {
      this.setState({
        attribute: attribute,
        filterType: USER_FILTER_TYPE.DATE_RANGE,
        GtLtThreshold: 0
      });
    } else if (attributeProperties.type === USER_FILTER_TYPE.INT_RANGE) {
      this.setState({
        attribute: attribute,
        filterType: USER_FILTER_TYPE.INT_RANGE,
        GtLtThreshold: 0
      });
    } else {
      this.setState({
        attribute: attribute,
        filterType: USER_FILTER_TYPE.DISCRETE,
        GtLtThreshold: 0,
        discreteSelected: [],
        discreteOptions: attributeProperties.values
      });
    }
  };

  attributeSelector = () => {
    let { possibleFilters } = this.props;
    const keys =
      possibleFilters !== undefined && possibleFilters !== null
        ? Object.keys(possibleFilters).filter(key => key !== "profile_picture")
        : [];

    return (
      <div
        key={this.state.selectorKeyBase + "AS"}
        style={{
          display: "flex",
          flexDirection: "row",
          alignItems: "center",
          flexFlow: "row wrap"
        }}
      >
        <Select
          showSearch
          defaultValue="Select Attribute"
          onChange={this.handleAttributeSelectorChange}
          style={{ width: "150px" }}
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
    );
  };

  comparatorChange = value => {
    this.setState({ comparator: value });
  };

  filterTypePicker = () => {
    let { filterType, attribute } = this.state;

    if (attribute === "select") {
      return <div />;
    }

    if (
      filterType === USER_FILTER_TYPE.DISCRETE ||
      filterType === USER_FILTER_TYPE.BOOLEAN_MAPPING
    ) {
      return <FilterText style={{ width: "45px" }}>one of</FilterText>;
    }

    return (
      <Select
        onChange={this.comparatorChange}
        defaultValue={"="}
        style={{ width: "150px" }}
      >
        <Option key={"="}>
          {filterType === USER_FILTER_TYPE.DATE_RANGE ? "on" : "is equal to"}
        </Option>
        <Option key={"<"}>
          {filterType === USER_FILTER_TYPE.DATE_RANGE
            ? "before"
            : "is less than"}
        </Option>
        <Option key={">"}>
          {filterType === USER_FILTER_TYPE.DATE_RANGE
            ? "after"
            : "is greater than"}
        </Option>
      </Select>
    );
  };

  handleDiscreteSelect = values => {
    this.setState({
      discreteSelected: values
    });
  };

  handleDateSelect = (date, dateString) => {
    this.setState({
      date: date
    });
  };

  handleNumericSet = value => {
    this.setState({
      GtLtThreshold: value
    });
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

    if (filterType === USER_FILTER_TYPE.DATE_RANGE) {
      return this.dateValuePicker();
    }
    return this.numericValuePicker();
  };

  discreteValuePicker = () => {
    let { possibleFilters } = this.props;

    let { attribute } = this.state;

    let valueArray =
      typeof possibleFilters[attribute].values !== "undefined"
        ? [...possibleFilters[attribute].values]
        : [];

    return (
      <Select
        mode="multiple"
        style={{ minWidth: "238px" }}
        placeholder="Please select"
        onChange={this.handleDiscreteSelect}
      >
        {valueArray.length !== 0
          ? valueArray.map(value => (
              <Option key={value}>{replaceUnderscores(value)}</Option>
            ))
          : null}
      </Select>
    );
  };

  dateValuePicker = () => {
    return <DatePicker onChange={this.handleDateSelect} />;
  };

  numericValuePicker = () => {
    return (
      <InputNumber
        type="number"
        style={{ width: "133px" }}
        onChange={this.handleNumericSet}
      />
    );
  };

  handleAddFilter = () => {
    let id = this.state.filters.length + 1;
    var newFilter;
    if (
      this.state.filterType === USER_FILTER_TYPE.DISCRETE ||
      this.state.filterType === USER_FILTER_TYPE.BOOLEAN_MAPPING
    ) {
      newFilter = {
        id: id,
        attribute: this.state.attribute,
        type: USER_FILTER_TYPE.DISCRETE,
        allowedValues: this.state.discreteSelected
      };
    } else if (this.state.filterType === USER_FILTER_TYPE.DATE_RANGE) {
      newFilter = {
        id: id,
        attribute: this.state.attribute,
        type: this.state.comparator,
        threshold: this.state.date.format("YYYY-MM-DD")
      };
    } else {
      let value = parseFloat(this.state.GtLtThreshold);
      newFilter = {
        id: id,
        attribute: this.state.attribute,
        type: this.state.comparator,
        threshold: value
      };
    }

    this.setState(
      prevstate => ({
        filters: [...prevstate.filters, newFilter],
        selectorKeyBase: `${Math.random()}`,
        ...this.baseRuleConstructionState
      }),
      () => {
        this.props.onFiltersChanged(this.state.filters);
      }
    );
  };

  addFilterBtn = () => {
    let { filterType } = this.state;
    let rowValues = Object.values({});
    let numberSelected = rowValues.filter(Boolean).length;
    let isSelected = numberSelected > 0 || filterType !== "of";
    var addFilterBtn = <div />;
    if (isSelected) {
      addFilterBtn = (
        <Button type="primary" onClick={this.handleAddFilter}>
          Add
        </Button>
      );
    }
    return addFilterBtn;
  };

  removeFilter = id => {
    this.setState(
      prevstate => ({
        filters: prevstate.filters.filter(filter => filter.id !== parseInt(id))
      }),
      () => {
        this.props.onFiltersChanged(this.state.filters);
      }
    );
  };

  activeFilterBubbles = () => {
    let { filters } = this.state;
    if (filters) {
      return (
        <div
          style={{
            display: "flex",
            flexDirection: "row",
            alignItems: "center",
            flexFlow: "row wrap"
          }}
        >
          {filters.map((filter, index) => {
            let attributeProperties = this.props.possibleFilters[
              filter.attribute
            ];

            let color =
              attributeProperties.table === "credit_transfer"
                ? DefaultTheme.primary
                : DefaultTheme.alt;

            let filterVals = <div />;

            if (
              filter.type === USER_FILTER_TYPE.DISCRETE ||
              filter.type === USER_FILTER_TYPE.BOOLEAN_MAPPING
            ) {
              filterVals = (
                <BubbleText style={{ color: color }}>
                  {filter.allowedValues.map((value, index) => {
                    if (filter.allowedValues.length === index + 1) {
                      return value;
                    } else {
                      return value + " or ";
                    }
                  })}
                </BubbleText>
              );
            } else {
              filterVals = (
                <BubbleText style={{ color: color }}>
                  {filter.type} {filter.threshold}
                </BubbleText>
              );
            }

            return (
              <FilterBubble
                key={index}
                onClick={() => this.removeFilter(filter.id)}
                style={{ borderColor: color }}
              >
                <BubbleLeft style={{ backgroundColor: color }}>
                  <BubbleText style={{ color: "#FFF" }}>
                    {attributeProperties.name}:
                  </BubbleText>
                </BubbleLeft>
                {filterVals}
                <SVG
                  src={
                    attributeProperties.table === "credit_transfer"
                      ? "/static/media/closePrimary.svg"
                      : "/static/media/closeAlt.svg"
                  }
                />
              </FilterBubble>
            );
          })}
        </div>
      );
    }
    return <div />;
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
          <PaddedInput>{this.attributeSelector()}</PaddedInput>

          <PaddedInput>{this.filterTypePicker()}</PaddedInput>

          <PaddedInput>{this.valuePicker()}</PaddedInput>

          <PaddedInput>{this.addFilterBtn()}</PaddedInput>
        </div>
        {this.activeFilterBubbles()}
      </div>
    );
  }
}

(Filter.defaultProps = defaultProps), (Filter.propTypes = propTypes);

export default Filter;

const PaddedInput = styled.div`
  margin: 10px;
`;

const FilterText = styled.p`
  white-space: nowrap;
  margin: 0;
  font: 200 14px system-ui;
  color: #777;
  -webkit-user-select: none; /* Chrome all / Safari all */
  -moz-user-select: none; /* Firefox all */
  -ms-user-select: none; /* IE 10+ */
  user-select: none;
`;

const FilterBubble = styled.div`
  display: flex;
  align-items: center;
  width: fit-content;
  margin: 10px 10px 10px 10px;
  height: 32px;
  padding: 0 10px 0 0;
  background-color: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 2px;
`;

const BubbleLeft = styled.div`
  display: flex;
  align-items: center;
  height: 32px;
  margin-left: -1px;
  border-radius: 2px 0 0 2px;
  background-color: #d9d9d9;
`;

const BubbleText = styled.p`
  white-space: nowrap;
  margin: 0;
  padding: 10px;
  font: 200 14px system-ui;
  color: #777;
  -webkit-user-select: none; /* Chrome all / Safari all */
  -moz-user-select: none; /* Firefox all */
  -ms-user-select: none; /* IE 10+ */
  user-select: none;
`;

const SVG = styled.img`
  width: 12px;
  height: 12px;
  cursor: pointer;
`;
