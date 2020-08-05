import React from "react";
import moment from "moment";

interface Props {
  created:
    | string
    | number
    | void
    | moment.Moment
    | Date
    | React.ReactText[]
    | moment.MomentInputObject
    | undefined;
}

export default function DateTime(props: Props) {
  const { created } = props;
  if (created) {
    var formatted_time = moment.utc(created).fromNow();

    return <div style={{ margin: 0 }}>{formatted_time}</div>;
  } else {
    return <div style={{ margin: 0 }}>Not long ago</div>;
  }
}
