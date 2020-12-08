import React, { Suspense, lazy } from "react";
import { connect } from "react-redux";
import {
  CenterLoadingSideBarActive,
  WrapperDiv,
  PageWrapper
} from "../styledElements";
import LoadingSpinner from "../loadingSpinner.jsx";
import FilterModule from "../filterModule/FilterModule";

const HeatMap = lazy(() => import("../heatmap/heatmap.jsx"));

const mapStateToProps = state => {
  return {
    metrics: state.metrics.metricsState,
    metricsLoadStatus: state.metrics.loadStatus,
    login: state.login
  };
};

class MapPage extends React.Component {
  constructor() {
    super();
    this.state = {};
  }

  render() {
    let {
      timeSeriesNameLabels,
      metrics,
      metricsLoadStatus,
      cardTitle,
      filterObject,
      defaultGroupBy,
      isMobile
    } = this.props;
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
            <FilterModule
              defaultGroupBy={"sender,coordinates"}
              filterObject={"credit_transfer"}
              dateRange={null}
              hideGroupBy={true}
            />
            <HeatMap />
          </PageWrapper>
        </WrapperDiv>
      </Suspense>
    );
  }
}

export default connect(mapStateToProps)(MapPage);
