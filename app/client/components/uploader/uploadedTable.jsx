import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";
import ReactTable from "react-table";

import { StyledButton, Input } from "../styledElements";

import { SpreadsheetAction } from "../../reducers/spreadsheet/actions";

const mapStateToProps = state => {
  return {
    saveState: state.datasetSave
  };
};

const mapDispatchToProps = dispatch => {
  return {
    saveDataset: body =>
      dispatch(SpreadsheetAction.saveDatasetRequest({ body })),
    resetUploadState: () => dispatch(SpreadsheetAction.resetUploadState())
  };
};

class uploadedTable extends React.Component {
  constructor() {
    super();
    this.state = {
      step: 0,
      selectedRow: null,
      selectedColumn: null,
      firstDataRow: null,
      headerPositions: {},
      customAttributeList: [],
      customAttribute: null,
      country: "",
      saveName: "",
      saveError: null
    };
    this.keyFunction = this.keyFunction.bind(this);
  }

  componentWillMount() {
    this.dataList = Object.keys(this.props.data.table_data).map(
      id => this.props.data.table_data[id]
    );
  }
  componentDidMount() {
    document.addEventListener("keydown", this.keyFunction, false);

    this.guessColumn(this.props.data.requested_attributes[0][0]);

    if (this.props.data.requested_attributes.length > 0) {
    }
  }
  componentWillUnmount() {
    this.props.resetUploadState();
    document.removeEventListener("keydown", this.keyFunction, false);
  }

  keyFunction(event) {
    if (event.keyCode === 13) {
      if (this.state.customAttribute === null) {
        this.handleNextClick();
      } else {
        this.handleAddClick();
      }
    }
  }

  currentStepNormalisedIndex() {
    return this.state.step - this.props.data.requested_attributes.length;
  }

  setHeader(headerName) {
    var headerPositions = this.state.headerPositions;

    headerPositions[this.state.selectedColumn] = headerName;
    this.setState({
      headerPositions: headerPositions
    });
  }

  unsetHeader(headerName) {
    var headerPositions = this.state.headerPositions;

    Object.keys(headerPositions).forEach(key => {
      if (headerPositions[key] === headerName) {
        delete headerPositions[key];

        this.setState({
          selectedColumn: key
        });
      }
    });

    this.setState({
      headerPositions: headerPositions
    });
  }

  clearSelected() {
    this.setState({
      selectedRow: null,
      selectedColumn: null
    });
  }

  processAndSaveDataset() {
    var dataset = {
      data: this.dataList.slice(this.state.firstDataRow),
      headerPositions: this.state.headerPositions,
      country: this.state.country,
      saveName: this.state.saveName,
      isVendor: this.props.is_vendor
    };

    this.props.saveDataset(dataset);
  }

  onCustomAttributeKeyPress(e) {
    console.log(e);
    var customAttribute = e.target.value;
    this.setState({ customAttribute: customAttribute });
    if (e.nativeEvent.keyCode != 13) return;
    this.handleAddClick();
  }

  handleCustomAttributeClick(attribute) {
    console.log(attribute);
    this.unsetHeader(attribute);

    var newCustomAttributeList = this.state.customAttributeList;

    var index = newCustomAttributeList.indexOf(attribute);
    if (index > -1) {
      newCustomAttributeList.splice(index, 1);
    }

    this.setState({ customAttributeList: newCustomAttributeList });
  }

  handleAddClick() {
    this.setHeader(this.state.customAttribute);

    var newcustomAttributeList = this.state.customAttributeList;
    newcustomAttributeList.push(this.state.customAttribute);

    this.setState({
      customAttribute: null,
      customAttributeList: newcustomAttributeList
    });

    this.clearSelected();
  }

  handleTableClick(e, column, rowInfo, instance) {
    console.log(this.currentStepNormalisedIndex());

    let normalised_index = this.currentStepNormalisedIndex();
    if (normalised_index < 0) {
      this.setState({
        selectedColumn:
          this.state.selectedColumn === column.id ? null : column.id
      });
    } else if (normalised_index === 0) {
      this.setState(
        {
          selectedColumn:
            this.state.selectedColumn === column.id ? null : column.id
        },
        () => {
          let first_row_item = this.props.data.table_data[0][
            this.state.selectedColumn
          ];
          if (first_row_item) {
            this.setState({ customAttribute: first_row_item });
          }
        }
      );
    } else if (normalised_index === 1) {
      this.setState({
        selectedRow:
          this.state.selectedRow === rowInfo.index ? null : rowInfo.index
      });
    }
  }

  onCountryInputKeyPress(e) {
    var country = e.target.value;
    this.setState({ country: country, saveError: null });
  }

  onSaveNameKeyPress(e) {
    var saveName = e.target.value;
    this.setState({ saveName: saveName, saveError: null });
    if (e.nativeEvent.keyCode != 13) return;
    this.handleNextClick();
  }

  guessColumn(requested_attribute_name) {
    let column_index_guess = this.props.data.column_firstrows[
      requested_attribute_name
    ];

    console.log("guess", column_index_guess);

    if (isFinite(column_index_guess)) {
      this.setState({
        selectedColumn: column_index_guess
      });
    }
  }

  handleStepIncrement(increment) {
    var current_step_index = this.state.step;
    var current_normalised_step_index =
      this.state.step - this.props.data.requested_attributes.length;

    var new_step_index = current_step_index + increment;
    var new_normalised_step_index = current_normalised_step_index + increment;

    //First handle the current step:
    if (current_normalised_step_index < 0) {
      var requested_attribute = this.props.data.requested_attributes[
        current_step_index
      ];
      this.setHeader(requested_attribute[0]);
    } else {
      switch (current_normalised_step_index) {
        case 0:
          break;
        case 1:
          this.setState({
            selectedRow: null,
            firstDataRow: this.state.selectedRow || 0
          });
          break;

        default:
          this.processAndSaveDataset();
          break;
      }
    }

    //Now handle the next step:

    this.clearSelected();

    if (new_normalised_step_index < 0) {
      let new_requested_attribute = this.props.data.requested_attributes[
        new_step_index
      ];
      this.unsetHeader(new_requested_attribute[0]);
      if (increment > 0) {
        this.guessColumn(new_requested_attribute[0]);
      }
    } else {
      switch (new_normalised_step_index) {
        case 0:
          break;
        case 1:
          this.setState({ firstDataRow: null });
          break;

        default:
          break;
      }
    }

    this.setState({
      step: Math.min(
        this.state.step + increment,
        this.props.data.requested_attributes.length + 2
      )
    });
  }

  handleNextClick() {
    this.handleStepIncrement(1);
  }

  handlePrevClick() {
    this.handleStepIncrement(-1);
  }

  render() {
    var columnList = Object.keys(this.dataList[0]).map(id => {
      return {
        Header:
          id in this.state.headerPositions
            ? this.state.headerPositions[id]
            : "",
        accessor: id.toString()
      };
    });

    var data = this.dataList.slice(this.state.firstDataRow);

    if (this.currentStepNormalisedIndex() === 0) {
      var stepSpecificFields = (
        <CustomColumnFields
          selectedColumn={this.state.selectedColumn}
          customAttributes={this.state.customAttributeList}
          customAttribute={this.state.customAttribute}
          onCustomAttributeKeyPress={e => this.onCustomAttributeKeyPress(e)}
          handleCustomAttributeClick={item =>
            this.handleCustomAttributeClick(item)
          }
          handleAddClick={() => this.handleAddClick()}
        />
      );
    } else {
      stepSpecificFields = (
        <StepSpecificFieldsContainer></StepSpecificFieldsContainer>
      );
    }

    if (this.props.saveState.saved) {
      var added = 0;
      var updated = 0;
      var errors = 0;

      var main_body = (
        <div>
          <PromptText>Save Complete</PromptText>
        </div>
      );
    } else {
      main_body = (
        <ReactTable
          data={data}
          columns={columnList}
          defaultPageSize={10}
          style={{ margin: "1em" }}
          sortable={false}
          getTheadThProps={(state, rowInfo, column, instance) => {
            return {
              onClick: e => this.handleTableClick(e, column, rowInfo, rowInfo),
              style: {
                height: "35px",
                fontWeight: 600,
                background: "#eee"
              }
            };
          }}
          getPaginationProps={() => {
            return {
              style: {
                display: "None"
              }
            };
          }}
          getTdProps={(state, rowInfo, column, instance) => {
            if (rowInfo) {
              var background =
                column.id == this.state.selectedColumn ||
                rowInfo.index == this.state.selectedRow
                  ? "#dff5f3"
                  : "white";
            } else {
              background =
                column.id == this.state.selectedColumn ? "#dff5f3" : "white";
            }

            var color =
              column.id in this.state.headerPositions ||
              this.state.firstDataRow == null
                ? "#666"
                : "#ccc";

            return {
              onClick: e => this.handleTableClick(e, column, rowInfo, instance),
              style: {
                background: background,
                color: color
              }
            };
          }}
        />
      );
    }

    let nextText = this.currentStepNormalisedIndex() === 2 ? "Save" : "Next";

    return (
      <PageWrapper>
        <Prompt
          step={this.state.step}
          promptText={this.state.promptText}
          is_vendor={this.props.is_vendor}
          saveState={this.props.saveState.saved}
          requested_attributes={this.props.data.requested_attributes}
        />

        <div
          style={{
            display: this.props.saveState.saved ? "none" : "flex",
            justifyContent: "space-between"
          }}
        >
          <StyledButton
            onClick={() => this.handlePrevClick()}
            style={
              this.state.step === 0 ||
              this.props.saveState.isRequesting ||
              this.props.saveState.saved
                ? { opacity: 0, pointerEvents: "None" }
                : {}
            }
            label={"Previous"}
          >
            Prev
          </StyledButton>

          <StyledButton
            onClick={() => this.handleNextClick()}
            style={
              this.props.saveState.isRequesting || this.props.saveState.saved
                ? { opacity: 0, pointerEvents: "None" }
                : {}
            }
            label={nextText}
          >
            {nextText}
          </StyledButton>
        </div>

        {stepSpecificFields}

        {main_body}
      </PageWrapper>
    );
  }
}

const SaveSheetFields = function(props) {
  if (props.isSaving) {
    return <StepSpecificFieldsContainer>Saving...</StepSpecificFieldsContainer>;
  }

  if (props.saved) {
    return (
      <StepSpecificFieldsContainer>
        <svg
          className="checkmark"
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 52 52"
        >
          <circle
            className="checkmark__circle"
            cx="26"
            cy="26"
            r="25"
            fill="none"
          />
          <path
            className="checkmark__check"
            fill="none"
            d="M14.1 27.2l7.1 7.2 16.7-16.8"
          />
        </svg>
        <p style={{ fontSize: "2em" }}>Save success!</p>
      </StepSpecificFieldsContainer>
    );
  }

  return <StepSpecificFieldsContainer></StepSpecificFieldsContainer>;
};

const CustomColumnFields = function(props) {
  if (props.selectedColumn) {
    return (
      <StepSpecificFieldsContainer>
        <CustomList
          customAttributes={props.customAttributes}
          handleClick={item => props.handleCustomAttributeClick(item)}
        />
        <div>Please add a label:</div>
        <CustomInput
          value={props.customAttribute}
          onCustomAttributeKeyPress={e => props.onCustomAttributeKeyPress(e)}
        />
        <StyledButton onClick={() => props.handleAddClick()} label={"Add"}>
          {" "}
          Add{" "}
        </StyledButton>
      </StepSpecificFieldsContainer>
    );
  } else {
    return (
      <StepSpecificFieldsContainer>
        <CustomList
          customAttributes={props.customAttributes}
          handleClick={item => props.handleCustomAttributeClick(item)}
        />
      </StepSpecificFieldsContainer>
    );
  }
};

class CustomInput extends React.Component {
  componentDidMount() {
    console.log(this.nameInput);
    this.nameInput.focus();
  }
  render() {
    return (
      <Input
        type="text"
        onChange={e => this.props.onCustomAttributeKeyPress(e)}
        placeholder="label"
        value={this.props.value}
        innerRef={input => {
          this.nameInput = input;
        }}
        aria-label={this.props.value}
      />
    );
  }
}

const CustomList = function(props) {
  return (
    <ListContainer>
      {props.customAttributes.map(item => (
        <ListItem key={item} onClick={() => props.handleClick(item)}>
          {item}

          <CloseIcon>X</CloseIcon>
        </ListItem>
      ))}
    </ListContainer>
  );
};

const Prompt = function(props) {
  let beneficiaryTermPlural = window.BENEFICIARY_TERM_PLURAL;

  var account_type = props.is_vendor ? "vendors" : `${beneficiaryTermPlural}`;

  if (props.step < props.requested_attributes.length) {
    var requested_key_display_name = props.requested_attributes[props.step][1];
    var text = `Which column contains the ${requested_key_display_name} of ${account_type}?`;
  } else {
    var later_step_index = props.step - props.requested_attributes.length;

    switch (later_step_index) {
      case 0:
        text = "Would you like to add any other custom columns?";
        break;
      case 1:
        text = "Which row is the first that contains data?";
        break;
      default:
        text = "Review and save your upload.";
        break;
    }
  }

  return (
    <PromptText style={{ display: props.saveState ? "none" : "block" }}>
      <div style={{ fontWeight: 700, display: "inline", marginRight: "0.5em" }}>
        Step {props.step + 1} of {props.requested_attributes.length + 3} :
      </div>
      {text}
    </PromptText>
  );
};

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(uploadedTable);

const PromptText = styled.div`
  font-size: 1.2em;
  font-weight: 400;
  color: #555;
`;

const ListContainer = styled.div`
  display: flex;
  flex-wrap: wrap;
  height: 38px;
`;

const ListItem = styled.div`
  display: inline-flex;
  margin: 0.25em;
  padding: 0.2em 0.5em;
  border-radius: 0.2rem;
  background: #c5c5c5;
  color: white;
`;

const StepSpecificFieldsContainer = styled.div`
  min-height: 120px;
`;

const CloseIcon = styled.div`
  color: #7b7b7b;
  margin-left: 1em;
  font-weight: 600;
`;

const PageWrapper = styled.div`
  margin: 1em;
  text-align: center;
`;
