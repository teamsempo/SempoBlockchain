import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";

const mapStateToProps = state => {
  return {};
};

const mapDispatchToProps = dispatch => {
  return {};
};

class DatasetFeedContainer extends React.Component {
  constructor() {
    super();
    this.state = {};
  }

  render() {
    return (
      <FeedContainer>
        {this.props.datasetList.map(item => {
          return (
            <FeedItem key={item.id}>
              <FeedName>{item.name}</FeedName>
              <MetaRow>
                <Country>{item.country}</Country>
                <Uploader>{item.uploader_email}</Uploader>
              </MetaRow>
            </FeedItem>
          );
        })}
      </FeedContainer>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(DatasetFeedContainer);

const FeedContainer = styled.div``;

const FeedItem = styled.div`
  min-width: 300px;
  margin: 0em 0.5em;
  padding: 0.5em 2em;
  border: 0px solid #e8e8e8;
  border-bottom-width: 1px;
  cursor: pointer;
  &:hover {
    background: #eee;
  }
`;

const FeedName = styled.div`
  font-size: 1.2em;
  text-decoration: underline;
  margin-bottom: 0.5em;
`;

const MetaRow = styled.div`
  display: flex;
  justify-content: space-between;
`;

const Country = styled.div`
  font-size: 1em;
`;

const Uploader = styled.div`
  font-size: 0.8em;
`;
