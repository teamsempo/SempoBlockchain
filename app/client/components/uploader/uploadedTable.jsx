import React from 'react';
import { connect } from 'react-redux';
import styled from 'styled-components';
import ReactTable from 'react-table';

import { StyledButton, Input, ErrorMessage } from '../styledElements';

import {
  saveDataset,
  resetUploadState,
} from '../../reducers/spreadsheetReducer';

const mapStateToProps = state => ({
  saveState: state.datasetSave,
});

const mapDispatchToProps = dispatch => ({
  saveDataset: body => dispatch(saveDataset({ body })),
  resetUploadState: () => dispatch(resetUploadState()),
});

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
      country: '',
      saveName: '',
      saveError: null,
    };
    this.keyFunction = this.keyFunction.bind(this);
  }

  componentWillMount() {
    this.dataList = Object.keys(this.props.data.table_data).map(
      id => this.props.data.table_data[id],
    );
  }

  componentDidMount() {
    document.addEventListener('keydown', this.keyFunction, false);

    this.guessColumn(this.props.data.requested_attributes[0][0]);

    if (this.props.data.requested_attributes.length > 0) {
    }
  }

  componentWillUnmount() {
    this.props.resetUploadState();
    document.removeEventListener('keydown', this.keyFunction, false);
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
    const { headerPositions } = this.state;

    headerPositions[this.state.selectedColumn] = headerName;
    this.setState({
      headerPositions,
    });
  }

  unsetHeader(headerName) {
    const { headerPositions } = this.state;

    Object.keys(headerPositions).forEach(key => {
      if (headerPositions[key] === headerName) {
        delete headerPositions[key];

        this.setState({
          selectedColumn: key,
        });
      }
    });

    this.setState({
      headerPositions,
    });
  }

  clearSelected() {
    this.setState({
      selectedRow: null,
      selectedColumn: null,
    });
  }

  processAndSaveDataset() {
    const dataset = {
      data: this.dataList.slice(this.state.firstDataRow),
      headerPositions: this.state.headerPositions,
      country: this.state.country,
      saveName: this.state.saveName,
      isVendor: this.props.is_vendor,
    };

    this.props.saveDataset(dataset);
  }

  onCustomAttributeKeyPress(e) {
    console.log(e);
    const customAttribute = e.target.value;
    this.setState({ customAttribute });
    if (e.nativeEvent.keyCode != 13) return;
    this.handleAddClick();
  }

  handleCustomAttributeClick(attribute) {
    console.log(attribute);
    this.unsetHeader(attribute);

    const newCustomAttributeList = this.state.customAttributeList;

    const index = newCustomAttributeList.indexOf(attribute);
    if (index > -1) {
      newCustomAttributeList.splice(index, 1);
    }

    this.setState({ customAttributeList: newCustomAttributeList });
  }

  handleAddClick() {
    this.setHeader(this.state.customAttribute);

    const newcustomAttributeList = this.state.customAttributeList;
    newcustomAttributeList.push(this.state.customAttribute);

    this.setState({
      customAttribute: null,
      customAttributeList: newcustomAttributeList,
    });

    this.clearSelected();
  }

  handleTableClick(e, column, rowInfo, instance) {
    console.log(this.currentStepNormalisedIndex());

    const normalised_index = this.currentStepNormalisedIndex();
    if (normalised_index < 0) {
      this.setState({
        selectedColumn:
          this.state.selectedColumn === column.id ? null : column.id,
      });
    } else if (normalised_index === 0) {
      this.setState(
        {
          selectedColumn:
            this.state.selectedColumn === column.id ? null : column.id,
        },
        () => {
          const first_row_item = this.props.data.table_data[0][
            this.state.selectedColumn
          ];
          if (first_row_item) {
            this.setState({ customAttribute: first_row_item });
          }
        },
      );
    } else if (normalised_index === 1) {
      this.setState({
        selectedRow:
          this.state.selectedRow === rowInfo.index ? null : rowInfo.index,
      });
    }
  }

  onCountryInputKeyPress(e) {
    const country = e.target.value;
    this.setState({ country, saveError: null });
  }

  onSaveNameKeyPress(e) {
    const saveName = e.target.value;
    this.setState({ saveName, saveError: null });
    if (e.nativeEvent.keyCode != 13) return;
    this.handleNextClick();
  }

  guessColumn(requested_attribute_name) {
    const column_index_guess = this.props.data.column_firstrows[
      requested_attribute_name
    ];

    console.log('guess', column_index_guess);

    if (isFinite(column_index_guess)) {
      this.setState({
        selectedColumn: column_index_guess,
      });
    }
  }

  handleStepIncrement(increment) {
    const current_step_index = this.state.step;
    const current_normalised_step_index =
      this.state.step - this.props.data.requested_attributes.length;

    const new_step_index = current_step_index + increment;
    const new_normalised_step_index = current_normalised_step_index + increment;

    // First handle the current step:
    if (current_normalised_step_index < 0) {
      const requested_attribute = this.props.data.requested_attributes[
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
            firstDataRow: this.state.selectedRow || 0,
          });
          break;

        default:
          this.processAndSaveDataset();
          break;
      }
    }

    // Now handle the next step:

    this.clearSelected();

    if (new_normalised_step_index < 0) {
      const new_requested_attribute = this.props.data.requested_attributes[
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
        this.props.data.requested_attributes.length + 2,
      ),
    });
  }

  handleNextClick() {
    this.handleStepIncrement(1);
  }

  handlePrevClick() {
    this.handleStepIncrement(-1);
  }

  render() {
    const columnList = Object.keys(this.dataList[0]).map(id => ({
      Header:
        id in this.state.headerPositions ? this.state.headerPositions[id] : '',
      accessor: id.toString(),
    }));

    const data = this.dataList.slice(this.state.firstDataRow);

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
      stepSpecificFields = <StepSpecificFieldsContainer />;
    }

    if (
      this.props.saveState.saved &&
      this.props.saveState.diagnostics.length > 0
    ) {
      let added = 0;
      let updated = 0;
      let errors = 0;

      const diagnostic_list = this.props.saveState.diagnostics.map(
        (diagnostic, index) => {
          if (diagnostic[1] !== 200) {
            errors += 1;
            return (
              <p style={{ size: '0.8em' }} key={index}>
                {diagnostic[0]}
              </p>
            );
          }
          if (diagnostic[0] === 'User Updated') {
            updated += 1;
          } else {
            added += 1;
            return null;
          }
        },
      );

      var main_body = (
        <div>
          <PromptText>Save Complete</PromptText>
          <p>
            <b>
              {' '}
              Added: {added}, Updated: {updated}, Errors: {errors}{' '}
            </b>
          </p>
          {diagnostic_list}
        </div>
      );
    } else {
      main_body = (
        <ReactTable
          data={data}
          columns={columnList}
          defaultPageSize={10}
          style={{ margin: '1em' }}
          sortable={false}
          getTheadThProps={(state, rowInfo, column, instance) => ({
            onClick: e => this.handleTableClick(e, column, rowInfo, rowInfo),
            style: {
              height: '35px',
              fontWeight: 600,
              background: '#eee',
            },
          })}
          getPaginationProps={() => ({
            style: {
              display: 'None',
            },
          })}
          getTdProps={(state, rowInfo, column, instance) => {
            if (rowInfo) {
              var background =
                column.id == this.state.selectedColumn ||
                rowInfo.index == this.state.selectedRow
                  ? '#dff5f3'
                  : 'white';
            } else {
              background =
                column.id == this.state.selectedColumn ? '#dff5f3' : 'white';
            }

            const color =
              column.id in this.state.headerPositions ||
              this.state.firstDataRow == null
                ? '#666'
                : '#ccc';

            return {
              onClick: e => this.handleTableClick(e, column, rowInfo, instance),
              style: {
                background,
                color,
              },
            };
          }}
        />
      );
    }

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
            display: this.props.saveState.saved ? 'none' : 'flex',
            justifyContent: 'space-between',
          }}>
          <StyledButton
            onClick={() => this.handlePrevClick()}
            style={
              this.state.step === 0 ||
              this.props.saveState.isRequesting ||
              this.props.saveState.saved
                ? { opacity: 0, pointerEvents: 'None' }
                : {}
            }>
            Prev
          </StyledButton>

          <StyledButton
            onClick={() => this.handleNextClick()}
            style={
              this.props.saveState.isRequesting || this.props.saveState.saved
                ? { opacity: 0, pointerEvents: 'None' }
                : {}
            }>
            {this.currentStepNormalisedIndex() === 2 ? 'Save' : 'Next'}
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
          viewBox="0 0 52 52">
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
        <p style={{ fontSize: '2em' }}>Save success!</p>
      </StepSpecificFieldsContainer>
    );
  }

  return <StepSpecificFieldsContainer />;
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
        <StyledButton onClick={() => props.handleAddClick()}>
          {' '}
          Add{' '}
        </StyledButton>
      </StepSpecificFieldsContainer>
    );
  }
  return (
    <StepSpecificFieldsContainer>
      <CustomList
        customAttributes={props.customAttributes}
        handleClick={item => props.handleCustomAttributeClick(item)}
      />
    </StepSpecificFieldsContainer>
  );
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
  const beneficiaryTermPlural = window.BENEFICIARY_TERM_PLURAL;

  const account_type = props.is_vendor ? 'vendors' : `${beneficiaryTermPlural}`;

  if (props.step < props.requested_attributes.length) {
    const requested_key_display_name =
      props.requested_attributes[props.step][1];
    var text = `Which column contains the ${requested_key_display_name} of ${account_type}?`;
  } else {
    const later_step_index = props.step - props.requested_attributes.length;

    switch (later_step_index) {
      case 0:
        text = 'Would you like to add any other custom columns?';
        break;
      case 1:
        text = 'Which row is the first that contains data?';
        break;
      default:
        text = 'Review and save your upload.';
        break;
    }
  }

  return (
    <PromptText style={{ display: props.saveState ? 'none' : 'block' }}>
      <div style={{ fontWeight: 700, display: 'inline', marginRight: '0.5em' }}>
        Step {props.step + 1} of {props.requested_attributes.length + 3} :
      </div>
      {text}
    </PromptText>
  );
};

export default connect(mapStateToProps, mapDispatchToProps)(uploadedTable);

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
  margin-left: 234px;
  width: calc(100vw - 234px);
  text-align: center;
`;
