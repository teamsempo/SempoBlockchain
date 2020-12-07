import React from "react";
import { connect } from "react-redux";

import { Input, Card, Divider } from "antd";
import { SearchOutlined } from "@ant-design/icons";

import matchSorter from "match-sorter";
import PropTypes from "prop-types";

import {
  LoadFilterAction,
  CreateFilterAction
} from "../../reducers/filter/actions";

import { USER_FILTER_TYPE } from "../../constants";

import Filter from "./filter";
import {
  generateQueryString,
  parseEncodedParamsForAccounts,
  parseQuery,
  processFiltersForQuery
} from "../../utils";
import { browserHistory } from "../../createStore";

const propTypes = {
  toggleTitle: PropTypes.string
};

const defaultProps = {
  toggleTitle: "Filters"
};

const mapStateToProps = state => {
  return {
    filters: state.filters,
    allowedFilters: state.allowedFilters.allowedFilterState
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadFilters: () => dispatch(LoadFilterAction.loadFilterRequest()),
    createFilter: body =>
      dispatch(CreateFilterAction.createFilterRequest({ body }))
  };
};

class SearchBoxWithFilter extends React.Component {
  constructor() {
    super();
    this.state = {
      phrase: "",
      encoded_filters: null,
      filters: [],
      possibleFilters: null,
      filterActive: false,
      dropdownActive: false,
      saveFilterDropdown: false,
      loadFiltersDropdown: false
    };
  }

  componentDidUpdate(newProps) {
    if (
      this.props.item_list !== newProps.item_list &&
      this.props.item_list.length > 0
    ) {
      let custom_attribute_dict = this.getPossibleFilters();
      this.setState({ possibleFilters: custom_attribute_dict });

      let query = parseQuery(location.search);
      if (query) {
        let decoded = parseEncodedParamsForAccounts(
          custom_attribute_dict,
          query["params"]
        );
        this.setState({
          filters: decoded || [],
          phrase: query["phrase"],
          encoded_filters: query["params"]
        });
      }
    }
  }

  saveFilter = () => {
    this.props.createFilter({
      filter_name: this.state.filterName,
      filter_attributes: this.state.filters
    });
  };

  loadFilters = () => {
    if (!this.state.loadFiltersDropdown) {
      // load filters hasn't been clicked
      this.props.loadFilters();
    }
    // toggle dropdown
    this.setState({ loadFiltersDropdown: !this.state.loadFiltersDropdown });
  };

  loadSavedFilter = filterId => {
    const savedFilter = this.props.filters.byId[filterId];
    this.setState({
      filters: savedFilter.filter,
      filterName: savedFilter.name
    });
  };

  getPossibleFilters = () => {
    var attribute_dict = {};
    var item_list = this.props.item_list;

    const proccess_attribute = (name, value) => {
      if (value !== undefined && value !== null) {
        if (attribute_dict[name] === undefined) {
          // This means that the attribute name has not been seen at all, which means we can just create array
          attribute_dict[name] = {
            name: name, // New filter module expects a name - quick fix before we do proper filters
            values: new Set([value]),
            type:
              typeof value == "number"
                ? USER_FILTER_TYPE.INT_RANGE
                : USER_FILTER_TYPE.DISCRETE
          };
        } else {
          // Attribute name has been seen, check if attribute VALUE has been seen
          if (!attribute_dict[name].values.has(value)) {
            //hasn't been seen, so add
            attribute_dict[name].values.add(value);
          }
        }
      }
    };

    if (item_list !== undefined) {
      // get attributes names and possible values
      item_list
        .filter(item => item.custom_attributes !== undefined)
        .map(item =>
          Object.keys(item.custom_attributes).map(attribute_name => {
            let attribute_value = item.custom_attributes[attribute_name];
            proccess_attribute(attribute_name, attribute_value);
          })
        );

      item_list.map(item => {
        Object.keys(this.props.filterKeys).map(key => {
          let attribute_value = item[key];
          if (this.props.filterKeys[key] !== null) {
            proccess_attribute(
              key,
              this.props.filterKeys[key](attribute_value)
            );
          } else {
            proccess_attribute(key, attribute_value);
          }
        });
      });
    }
    return attribute_dict;
  };

  onFiltersChanged = filters => {
    let encoded_filters = processFiltersForQuery(filters);
    this.setState(
      {
        filters,
        encoded_filters
      },
      this.buildQuery
    );
  };

  handleChange = evt => {
    this.setState({ [evt.target.name]: evt.target.value }, () =>
      this.buildQuery()
    );
  };

  buildQuery() {
    let { encoded_filters, phrase } = this.state;
    let params = {};
    if (encoded_filters) {
      params.params = encoded_filters;
    }
    if (phrase) {
      params.phrase = phrase;
    }
    let searchQuery = generateQueryString(params);
    browserHistory.push({
      search: searchQuery
    });
  }

  applyFilter = (item_list, filter) => {
    return item_list.reduce((filtered, item) => {
      let added = false;

      const add_account = () => {
        filtered.push(item);
        added = true;
      };

      const test_conditions = (filter, value) => {
        if (
          filter.type === USER_FILTER_TYPE.DISCRETE ||
          filter.type === USER_FILTER_TYPE.BOOLEAN_MAPPING
        ) {
          if (filter.allowedValues.includes((value || "").toString())) {
            // attribute value is in allowed value, add account to filtered
            add_account();
          }
        } else if (filter.type === "<") {
          if (value < filter.threshold) {
            add_account();
          }
        } else if (filter.type === ">") {
          if (value > filter.threshold) {
            add_account();
          }
        }
      };

      //Filtering Standard Attributes
      Object.keys(item).map(attribute_name => {
        let key = filter.attribute;
        if (attribute_name === key) {
          // attribute name matches key name, apply filter test
          var attribute_value = item[attribute_name];
          if (this.props.filterKeys[key] !== null) {
            attribute_value = this.props.filterKeys[key](attribute_value);
          }

          test_conditions(filter, attribute_value);
        }
      });

      if (added === false && item.custom_attributes !== undefined) {
        //Filtering Custom Attributes
        Object.keys(item.custom_attributes).map(attribute_name => {
          if (attribute_name === filter.attribute) {
            let attribute_value = item.custom_attributes[attribute_name];
            test_conditions(filter, attribute_value);
          }
        });
      }

      return filtered;
    }, []);
  };

  render() {
    const { phrase, filters } = this.state;

    var item_list = this.props.item_list;

    // Phrase Search
    if (phrase !== "") {
      item_list = matchSorter(item_list, this.state.phrase, {
        keys: this.props.searchKeys
      });
    }

    if (filters.length > 0 && item_list.length > 0) {
      this.state.filters.map(filter => {
        item_list = this.applyFilter(item_list, filter);
      });
    }

    return (
      <div>
        <Card style={{ width: "calc(100% - 2em)", margin: "1em 1em 0em" }}>
          <Input
            prefix={<SearchOutlined />}
            size="large"
            name="phrase"
            value={phrase}
            placeholder="Search..."
            onChange={this.handleChange}
          />
          <Divider dashed />
          <Filter
            filters={filters} // this is only used for initial load
            possibleFilters={this.state.possibleFilters}
            onFiltersChanged={this.onFiltersChanged}
          />
        </Card>

        <div>
          {React.cloneElement(this.props.children, { item_list: item_list })}
        </div>
      </div>
    );
  }
}

(SearchBoxWithFilter.defaultProps = defaultProps),
  (SearchBoxWithFilter.propTypes = propTypes);

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(SearchBoxWithFilter);
