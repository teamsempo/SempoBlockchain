import React from "react";
import { connect } from "react-redux";
import { Card } from "antd";

import { CenterLoadingSideBarActive, WrapperDiv } from "../styledElements.js";

import { LoadCreditTransferAction } from "../../reducers/creditTransfer/actions";
import organizationWrapper from "../organizationWrapper.jsx";
import LoadingSpinner from "../loadingSpinner";

const mapStateToProps = state => {
  return {
    creditTransfers: state.creditTransfers
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadCreditTransferList: path =>
      dispatch(LoadCreditTransferAction.loadCreditTransferListRequest(path))
  };
};

class SingleCreditTransferPage extends React.Component {
  componentDidMount() {
    let pathname_array = location.pathname.split("/").slice(1);
    let creditTransferId = parseInt(pathname_array[1]);
    this.props.loadCreditTransferList({ path: creditTransferId });
  }

  render() {
    let pathname_array = location.pathname.split("/").slice(1);
    let url_provided = pathname_array[1];
    let creditTransferId = parseInt(url_provided);

    let creditTransferComponent;
    if (this.props.creditTransfers.byId[creditTransferId]) {
      creditTransferComponent = <div>Single Credit Transfer</div>;
    } else {
      creditTransferComponent = (
        <Card style={{ textAlign: "center" }}>
          <p>No Such Credit Transfer: {url_provided}</p>
        </Card>
      );
    }

    if (this.props.creditTransfers.loadStatus.isRequesting === true) {
      return (
        <WrapperDiv>
          <CenterLoadingSideBarActive>
            <LoadingSpinner />
          </CenterLoadingSideBarActive>
        </WrapperDiv>
      );
    } else {
      return <div>{creditTransferComponent}</div>;
    }
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(organizationWrapper(SingleCreditTransferPage));
