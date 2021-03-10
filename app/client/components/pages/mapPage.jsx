import React, { lazy } from "react";
import { connect } from "react-redux";
import { Card } from "antd";
import { WrapperDiv, PageWrapper } from "../styledElements";
import LoadingSpinner from "../loadingSpinner.jsx";
import FilterModule from "../filterModule/FilterModule";
import NoDataMessage from "../NoDataMessage";

const HeatMap = lazy(() => import("../heatmap/heatmap.jsx"));

const mapStateToProps = state => {
  return {
    metricsLoadStatus: state.metrics.loadStatus
  };
};

class MapPage extends React.Component {
  constructor() {
    super();
  }

  render() {
    return (
      <WrapperDiv>
        <PageWrapper>
          {this.props.metricsLoadStatus.success ? (
            <div>
              <Card
                style={{
                  position: "fixed",
                  top: 0,
                  zIndex: 1,
                  margin: "1em",
                  maxWidth: "calc(100vw - 2em)"
                }}
              >
                <FilterModule
                  defaultGroupBy={"sender,coordinates"}
                  filterObject={"credit_transfer"}
                  dateRange={null}
                  hideGroupBy={true}
                />
              </Card>
              <HeatMap />
            </div>
          ) : this.props.metricsLoadStatus.isRequesting ? (
            <LoadingSpinner />
          ) : (
            <NoDataMessage />
          )}
        </PageWrapper>
      </WrapperDiv>
    );
  }
}

export default connect(mapStateToProps)(MapPage);
