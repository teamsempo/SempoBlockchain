/* global window,document */
import React, { Component, lazy, Suspense } from "react";
import { connect } from "react-redux";

import MapGL from "react-map-gl";
import DeckGLOverlay from "./deckglOverlay.jsx";

// Set your mapbox token here
const MAPBOX_TOKEN =
  "pk.eyJ1Ijoic2VtcG9uaWNrIiwiYSI6ImNqZnJtNHkybzA0OWMyd25lczcyeXJwMTYifQ.0CJmw4sMU_VuX4wsPlb53Q"; // eslint-disable-line

// Source data CSV
const DATA_URL =
  "https://raw.githubusercontent.com/uber-common/deck.gl-data/master/examples/3d-heatmap/heatmap-data.csv"; // eslint-disable-line

const mapStateToProps = state => {
  return {
    creditTransferLocationList: Object.keys(state.creditTransfers.byId)
      .map(id => state.creditTransfers.byId[id])
      // .filter(d => d.transfer_type === "PAYMENT")
      .filter(d => !isNaN(d.lng))
      .filter(d => !isNaN(d.lat))
      .map(d => [Number(d.lng), Number(d.lat)]),
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
        longitude: this.props.activeOrganisation.default_lng || 144,
        latitude: this.props.activeOrganisation.default_lat || -1
      },
      data: null
    };
  }

  componentDidMount() {
    console.log("list", this.props.creditTransferLocationList);
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

    var data = this.props.creditTransferLocationList;

    data.push([0, 0]);

    return (
      <MapGL
        {...viewport}
        mapStyle="mapbox://styles/mapbox/dark-v9"
        onViewportChange={this._onViewportChange.bind(this)}
        mapboxApiAccessToken={MAPBOX_TOKEN}
      >
        <DeckGLOverlay viewport={viewport} data={data || []} />
      </MapGL>
    );
  }
}

export default connect(
  mapStateToProps,
  null
)(HeatMap);
