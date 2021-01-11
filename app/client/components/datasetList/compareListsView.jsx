import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";

import { SpreadsheetAction } from "../../reducers/spreadsheet/actions";

import DatasetFeed from "./datasetFeed.jsx";
import LoadingSpinner from "../loadingSpinner.jsx";

const mapStateToProps = state => {
  return {
    datasetList: state.datasetList,
    login: state.login,
    loggedIn: state.login.token != null
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadDatasetList: payload =>
      dispatch(SpreadsheetAction.loadDatasetListRequest())
  };
};

class CompareListsView extends React.Component {
  constructor() {
    super();
    this.state = {};
  }

  componentDidMount() {
    this.props.loadDatasetList();
  }

  componentWillReceiveProps(nextProps) {
    if (nextProps.loggedIn !== this.props.loggedIn) {
      this.props.loadDatasetList();
    }
  }

  render() {
    if (Object.keys(this.props.datasetList.data).length === 0) {
      return <LoadingSpinner />;
    }

    return (
      <div style={{ display: "flex", marginTop: "1em" }}>
        <FeedContainer>
          <div style={{ fontWeight: 600 }}>Merge:</div>
          <FeedTitle>Your Datasets</FeedTitle>
          <DatasetFeed
            datasetList={Object.keys(this.props.datasetList.data)
              .map(key => this.props.datasetList.data[key])
              .filter(item => item.uploader_id === this.props.login.userId)}
          />
        </FeedContainer>

        <FeedContainer>
          <div style={{ fontWeight: 600 }}>With:</div>
          <FeedTitle>Other Datasets</FeedTitle>
          <DatasetFeed
            datasetList={Object.keys(this.props.datasetList.data)
              .map(key => this.props.datasetList.data[key])
              .filter(item => item.uploader_id !== this.props.login.userId)}
          />
        </FeedContainer>
      </div>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(CompareListsView);

const FeedContainer = styled.div`
  margin: 2em;
`;

const FeedTitle = styled.div`
  font-size: 1.5em;
  margin-bottom: 0.5em;
`;
