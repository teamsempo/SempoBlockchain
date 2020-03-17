import React from "react";
import { connect } from "react-redux";

import { Link } from "react-router-dom";
import { modifyTransferRequest } from "../../reducers/creditTransferReducer";

const mapStateToProps = state => {
  return {
    creditTransfers: state.creditTransfers,
    users: state.users
  };
};

const mapDispatchToProps = dispatch => {
  return {
    modifyTransferRequest: (body, path) =>
      dispatch(modifyTransferRequest({ body, path }))
  };
};

class userCell extends React.Component {
  render() {
    if (this.props.user_id) {
      var user = this.props.users.byId[this.props.user_id];

      if (user) {
        return (
          <Link
            to={"/users/" + this.props.user_id}
            style={{
              color: "inherit",
              textDecoration: "inherit",
              display: "flex",
              flexDirection: "column",
              alignItems: "center"
            }}
          >
            {user.first_name} {user.last_name}
          </Link>
        );
      }
    }

    return <div>-</div>;
  }
}

export default connect(
  mapStateToProps,
  mapDispatchToProps
)(userCell);
