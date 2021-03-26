import React from "react";
import moment from "moment";

interface Props {
  useRelativeTime: Boolean;
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
  const useRelativeTime = props.useRelativeTime || false;
  if (created) {
    const formatted_time = useRelativeTime
      ? moment.utc(created).fromNow()
      : moment
          .utc(created)
          .local()
          .format("YYYY-MM-DD HH:mm:ss");
    return <div style={{ margin: 0 }}>{formatted_time}</div>;
  } else {
    return <div style={{ margin: 0 }}>Unknown</div>;
  }
}
