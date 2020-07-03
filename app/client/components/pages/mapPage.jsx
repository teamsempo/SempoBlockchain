import React, { Suspense, lazy } from "react";
import { connect } from "react-redux";
import {
  CenterLoadingSideBarActive,
  WrapperDiv,
  PageWrapper
} from "../styledElements";
import LoadingSpinner from "../loadingSpinner.jsx";
import { LoadCreditTransferAction } from "../../reducers/creditTransfer/actions";
import { CreditTransferFiltersAction } from "../../reducers/creditTransferFilter/actions";
import NoDataMessage from "../NoDataMessage";

const HeatMap = lazy(() => import("../heatmap/heatmap.jsx"));

const mapStateToProps = state => {
  return {
    creditTransfers: state.creditTransfers,
    login: state.login
  };
};

const mapDispatchToProps = dispatch => {
  return {
    loadCreditTransferList: query =>
      dispatch(
        LoadCreditTransferAction.loadCreditTransferListRequest({ query })
      ),
    loadCreditTransferFilters: () =>
      dispatch(CreditTransferFiltersAction.loadCreditTransferFiltersRequest())
  };
};

class MapPage extends React.Component {
  constructor() {
    super();
    this.state = {};
  }

  componentDidMount() {
    let transfer_type = "ALL";
    let per_page = 50;
    let page = 1;
    this.props.loadCreditTransferList({
      get_stats: true,
      transfer_type: transfer_type,
      per_page: per_page,
      page: page
    });

    this.props.loadCreditTransferFilters();
  }

  render() {
    if (this.props.creditTransfers.loadStatus.isRequesting === true) {
      return (
        <WrapperDiv>
          <CenterLoadingSideBarActive>
            <LoadingSpinner />
          </CenterLoadingSideBarActive>
        </WrapperDiv>
      );
    } else if (Object.values(this.props.creditTransfers.byId).length === 0) {
      return (
        <PageWrapper>
          <NoDataMessage />
        </PageWrapper>
      );
    } else if (this.props.creditTransfers.loadStatus.success === true) {
      return (
        <Suspense
          fallback={
            <CenterLoadingSideBarActive>
              <LoadingSpinner />
            </CenterLoadingSideBarActive>
          }
        >
          <WrapperDiv>
            <PageWrapper>
              <HeatMap />
            </PageWrapper>
          </WrapperDiv>
        </Suspense>
      );
    } else {
      return (
        <WrapperDiv>
          <p>Something went wrong.</p>
        </WrapperDiv>
      );
    }
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(MapPage);
