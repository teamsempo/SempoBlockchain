import React from "react";
import moment from "moment";

export default class DateTime extends React.Component {
  render() {
    if (this.props.created) {
      var formatted_time = new Date(this.props.created).toDateString();

      return <div style={{ margin: 0 }}>{formatted_time}</div>;
    } else {
      return <div style={{ margin: 0 }}>Not long ago</div>;
    }
  }
}
