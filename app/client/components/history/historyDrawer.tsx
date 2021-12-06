import React from "react";
import { Drawer, Timeline } from "antd";
import { connect } from "react-redux";
import { toTitleCase, replaceUnderscores } from "../../utils";
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
    const stringList = this.props.changes.map(change => {
      return `${toTitleCase(
        replaceUnderscores(change.column_name)
      )} changed from "${change.old_value}" to "${change.new_value}" by ${
        change.change_by.email
      }`;
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
          {stringList.map(item => (
            <Timeline.Item>{item}</Timeline.Item>
          ))}
        </Timeline>
      </Drawer>
    );
  }
}

export default connect()(HistoryDrawer);
