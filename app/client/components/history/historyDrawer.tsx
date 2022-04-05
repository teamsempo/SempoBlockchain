import React from "react";
import { Drawer, Timeline } from "antd";
import { connect } from "react-redux";
import { toTitleCase, replaceUnderscores } from "../../utils";
import DateTime from "../dateTime";

interface Props {
  drawerVisible: boolean;
  onClose: any;
  changes: [];
}

class HistoryDrawer extends React.Component<Props> {
  constructor(props: any) {
    super(props);
  }

  render() {
    const stringList = this.props.changes.map((change) => {
      const email = change.change_by ? change.change_by.email : "Unknown";
      const old_value = change.old_value ? change.old_value : "null";
      const new_value = change.new_value ? change.new_value : "null";
      const column_name = toTitleCase(replaceUnderscores(change.column_name));
      const created = change.created;
      return {
        item: `${toTitleCase(
          replaceUnderscores(column_name)
        )} changed from "${old_value}" to "${new_value}"`,
        date: created,
        email: email,
      };
    });

    return (
      <Drawer
        title="Account History"
        placement="right"
        visible={this.props.drawerVisible}
        onClose={this.props.onClose}
        width={500}
      >
        <Timeline>
          {stringList.map((item, index) => (
            <Timeline.Item key={index}>
              {item.item} by <a href={"mailto://" + item.email}>{item.email}</a>{" "}
              at <DateTime created={item.date} useRelativeTime={false} />
            </Timeline.Item>
          ))}
        </Timeline>
      </Drawer>
    );
  }
}

export default connect()(HistoryDrawer);
