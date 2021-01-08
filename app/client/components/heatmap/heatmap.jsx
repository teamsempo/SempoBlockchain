/* global window,document */
import React, { Component, lazy, Suspense } from "react";
import { connect } from "react-redux";

import MapGL from "react-map-gl";
import DeckGLOverlay from "./deckglOverlay.jsx";

const mapStateToProps = state => {
  const transactionCounts = state.metrics.metricsState.daily_transaction_count
    ? state.metrics.metricsState.daily_transaction_count.aggregate
    : [];
  let coords = [];
  Object.keys(transactionCounts).forEach(coordonate => {
    if (!["None", "percent_change", "total", null].includes(coordonate)) {
      const parsedCoordinate = coordonate
        .split(",")
        .map(pc => parseFloat(pc))
        .reverse();
      coords = [
        ...coords,
        ...Array(transactionCounts[coordonate]).fill(parsedCoordinate)
      ];
    }
  });
  return {
    metrics: coords,
    activeOrganisation: state.organisations.byId[state.login.organisationId]
  };
};

class HeatMap extends Component {
  constructor(props) {
    super(props);
    this.state = {
      viewport: {
        ...DeckGLOverlay.defaultViewport,
        width: 500,
        height: 500,
        latitude: this.props.activeOrganisation.default_lat || -17.73,
        longitude: this.props.activeOrganisation.default_lng || 168.29
      },
      data: null
    };
  }

  componentDidMount() {
    window.addEventListener("resize", this._resize.bind(this));
    this._resize();
  }

  _resize() {
    this._onViewportChange({
      width: window.innerWidth,
      height: window.innerHeight
    });
  }

  _onViewportChange(viewport) {
    this.setState({
      viewport: { ...this.state.viewport, ...viewport }
    });
  }

  render() {
    const viewport = this.state.viewport;
    return (
      <MapGL
        {...viewport}
        mapStyle="mapbox://styles/mapbox/dark-v9"
        onViewportChange={this._onViewportChange.bind(this)}
        mapboxApiAccessToken={window.MAPBOX_TOKEN}
      >
        <DeckGLOverlay viewport={viewport} data={this.props.metrics || []} />
      </MapGL>
    );
  }
}

export default connect(
  mapStateToProps,
  null
)(HeatMap);
