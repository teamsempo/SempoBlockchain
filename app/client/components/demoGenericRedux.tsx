import * as React from "react";
import { connect } from "react-redux";

import { ReduxState, sempoObjects } from "../reducers/rootReducer";

import { LoadRequestAction } from "../genericState";
import { apiActions } from "../genericState";

interface StateProps {
  UserExample: any;
}

interface DispatchProps {
  loadUsers: () => LoadRequestAction;
}

type Props = StateProps & DispatchProps;

const mapStateToProps = (state: ReduxState): StateProps => {
  return {
    UserExample: state.UserExample
  };
};

const mapDispatchToProps = (dispatch: any): DispatchProps => {
  return {
    loadUsers: () => dispatch(apiActions.load(sempoObjects.UserExample))
  };
};

//Currently loaded into settings page, uncomment there to see it work
class DemoGenericRedux extends React.Component<Props> {
  componentDidMount() {
    this.props.loadUsers();
  }

  render() {
    return <></>;
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(DemoGenericRedux);
