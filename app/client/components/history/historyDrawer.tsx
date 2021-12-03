import React from "react";
import { Drawer, Timeline } from "antd";
import { connect } from "react-redux";
import { toTitleCase, replaceUnderscores } from "../../utils";
import { LoadTransferAccountHistoryAction } from "../../reducers/transferAccount/actions";
import { LoadTransferAccountHistoryPayload } from "../../reducers/transferAccount/types";
import { ReduxState } from "../../reducers/rootReducer";
import internal from "assert";

interface Props {
  drawerVisible: boolean;
  onClose: any;
  id: number;
  LoadTransferAccountHistoryAction: (
    path: number
  ) => typeof LoadTransferAccountHistoryAction;
  transferAccountHistory: [];
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

const mapStateToProps = (state: ReduxState): any => {
  return {
    transferAccountHistory: state.transferAccounts.loadHistory.changes
  };
};

class HistoryDrawer extends React.Component<Props> {
  constructor(props: any) {
    super(props);
  }

  componentDidMount() {
    this.props.LoadTransferAccountHistoryAction(this.props.id);
  }

  render() {
    const stringList = this.props.transferAccountHistory.map(change => {
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
  mapStateToProps,
  mapDispatchToProps
)(HistoryDrawer);
