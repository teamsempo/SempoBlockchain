import React, { Suspense, lazy } from "react";
import { CenterLoadingSideBarActive } from "../styledElements";
import LoadingSpinner from "../loadingSpinner.jsx";

const HeatMap = lazy(() => import("../heatmap/heatmap.jsx"));

export default class MapPage extends React.Component {
  constructor() {
    super();
    this.state = {};
  }

  render() {
    return (
      <Suspense
        fallback={
          <CenterLoadingSideBarActive>
            <LoadingSpinner />
          </CenterLoadingSideBarActive>
        }
      >
        <HeatMap />
      </Suspense>
    );
  }
}
