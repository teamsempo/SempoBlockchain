import React from "react";
import { connect } from "react-redux";
import { Button } from "antd";

import { browserHistory } from "../../createStore.js";
import { PageWrapper, WrapperDiv, StyledButton } from "../styledElements.js";
import { LightTheme } from "../theme.js";

import BulkDisbursementTransferAccountList from "../transferAccount/BulkDisbursementTransferAccountList";

import { LoadTransferAccountAction } from "../../reducers/transferAccount/actions";
import organizationWrapper from "../organizationWrapper.jsx";
import NoDataMessage from "../NoDataMessage";
import QueryConstructor from "../filterModule/queryConstructor";
import { LoadBulkTransfersAction } from "../../reducers/bulkTransfer/actions";
import { CreateBulkTransferBody } from "../../reducers/bulkTransfer/types";
import { apiActions } from "../../genericState";
import { sempoObjects } from "../../reducers/rootReducer";

const mapStateToProps = state => {
  return {
    login: state.login,
    bulkTransfers: state.BULK
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadBulkDisbursement: path =>
      dispatch(apiActions.load(sempoObjects.BULK, path)),
    modifyBulkDisbursement: (path, body) =>
      dispatch(apiActions.modify(sempoObjects.BULK, path, body))
  };
};

class SingleBulkDisbursementPage extends React.Component {
  componentDidMount() {
    let bulkId = this.props.match.params.bulkId;
    this.props.loadBulkDisbursement(bulkId);
  }

  onConfirm() {
    let bulkId = this.props.match.params.bulkId;

    this.props.modifyBulkDisbursement(bulkId, { action: "EXECUTE" });
  }

  render() {
    let bulkId = this.props.match.params.bulkId;

    let transfer = this.props.bulkTransfers.byId[bulkId];

    return (
      <WrapperDiv>
        <PageWrapper>
          <Button onClick={() => this.onConfirm()}>
            {transfer && transfer.recipient_count}
          </Button>
        </PageWrapper>
      </WrapperDiv>
    );
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(organizationWrapper(SingleBulkDisbursementPage));
