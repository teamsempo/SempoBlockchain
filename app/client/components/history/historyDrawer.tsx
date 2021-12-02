import React from "react";
import { Drawer, Timeline } from "antd";
import { connect } from "react-redux";
import { toTitleCase, replaceUnderscores } from "../../utils";
import { LoadTransferAccountHistoryAction } from "../../reducers/transferAccount/actions";
import { LoadTransferAccountHistoryPayload } from "../../reducers/transferAccount/types";

interface Props {
  drawerVisible: boolean;
  onClose: any;
  LoadTransferAccountHistoryAction: () => typeof LoadTransferAccountHistoryAction;
}

const mapDispatchToProps = (dispatch: any) => {
  return {
    LoadTransferAccountHistoryAction: (path: number) =>
      dispatch(
        LoadTransferAccountHistoryAction.loadTransferAccountHistoryRequest({
          path
        })
      )
  };
};

const data = {
  data: {
    changes: [
      {
        change_by: {
          email: "michiel@withsempo.com",
          first_name: null,
          id: 1,
          last_name: null
        },
        column_name: "notes",
        created: "2021-11-29T20:30:19.014788+00:00",
        new_value: "This is a test note",
        old_value: "abcsef"
      }
    ]
  },
  message: "Successfully Loaded.",
  status: "success"
};

class HistoryDrawer extends React.Component<Props> {
  constructor(props: any) {
    super(props);
  }

  render() {
    if (this.props.drawerVisible) {
      this.props.LoadTransferAccountHistoryAction(4);
    }
    const stringList = data.data.changes.map(change => {
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

export default connect(
  null,
  mapDispatchToProps
)(HistoryDrawer);
