import React from "react";
import { connect } from "react-redux";
import styled from "styled-components";

import AsyncButton from "../AsyncButton.jsx";

import { Input, ErrorMessage } from "../styledElements";
import { InviteUserAction } from "../../reducers/auth/actions";

const mapStateToProps = state => {
  return {
    createAdminStatus: state.adminUsers.createStatus
  };
};

const mapDispatchToProps = dispatch => {
  return {
    inviteUser: body => dispatch(InviteUserAction.inviteUserRequest({ body }))
  };
};

export class InviteFormContainer extends React.Component {
  constructor() {
    super();
    this.state = {
      email: "",
      email_missing: false,
      invalid_request: false,
      tier: "view"
    };
  }

  componentWillReceiveProps(nextProps) {
    this.setState({ invalid_request: nextProps.createAdminStatus.error });
  }

  attemptlogin() {
    if (this.state.email == "") {
      this.setState({ email_missing: true });
      return;
    }
    this.props.inviteUser({ email: this.state.email, tier: this.state.tier });
  }

  onEmailFieldKeyPress(e) {
    let email = e.target.value;
    this.setState({
      email: email,
      email_missing: false,
      invalid_request: false
    });
    if (e.nativeEvent.keyCode != 13) return;
    this.attemptlogin();
  }

  onClick() {
    this.attemptlogin();
  }

  handleToggle(evt) {
    this.setState({ tier: evt.target.value });
  }

  render() {
    return (
      <InviteForm
        handleToggle={evt => this.handleToggle(evt)}
        onEmailFieldKeyPress={e => this.onEmailFieldKeyPress(e)}
        onClick={() => this.onClick()}
        email_missing={this.state.email_missing}
        invalid_request={this.state.invalid_request}
        isLoggingIn={this.props.createAdminStatus.isRequesting}
        tier={this.state.tier}
      />
    );
  }
}

const InviteForm = function(props) {
  if (props.email_missing) {
    var error_message = "Email Missing";
  } else if (props.invalid_request !== false) {
    error_message = props.invalid_request;
  } else {
    error_message = "";
  }

  const tiers = ["superadmin", "admin", "subadmin", "view"];

  return (
    <div>
      <div style={{ display: "block" }}>
        <Input
          type="email"
          id="EmailField"
          onKeyUp={props.onEmailFieldKeyPress}
          placeholder="Email"
          aria-label="Email"
        />

        <RoleTypeWrapper>
          {tiers.map((tier, i) => {
            return (
              <LabelContainer key={i}>
                {tier}
                <LabelInput
                  type="radio"
                  value={tier}
                  checked={props.tier === tier}
                  onChange={props.handleToggle}
                  aria-label={`Tier ${tier}`}
                />
                <LabelCheckmark checked={props.tier === tier} />
              </LabelContainer>
            );
          })}
        </RoleTypeWrapper>
      </div>

      <ErrorMessage>{error_message}</ErrorMessage>

      <AsyncButton
        onClick={props.onClick}
        isLoading={props.isLoggingIn}
        buttonStyle={{ width: "calc(100% - 1em)", display: "flex" }}
        buttonText={<span>Invite</span>}
        label={"Invite"}
      />
    </div>
  );
};
export default connect(
  mapStateToProps,
  mapDispatchToProps
)(InviteFormContainer);

const RoleTypeWrapper = styled.div`
  margin: 0.5em;
`;

const LabelContainer = styled.label`
  text-transform: capitalize;
  font-size: 14px;
  font-weight: 500;
  line-height: 15px;
  display: block;
  position: relative;
  padding: 10px 0 10px 30px;
  cursor: pointer;
  -webkit-user-select: none;
  -moz-user-select: none;
  -ms-user-select: none;
  user-select: none;
`;

const LabelInput = styled.input`
  position: absolute;
  opacity: 0;
  cursor: pointer;
  display: block;
`;

const LabelCheckmark = styled.span`
  position: absolute;
  top: 10px;
  left: 0;
  height: 14px;
  width: 14px;
  background-color: ${props => (props.checked ? "#2d9ea0" : "#eee")};
  border-radius: 50%;
  :after {
    content: "";
    position: absolute;
    display: ${props => (props.checked ? "block" : "none")};
    top: 4px;
    left: 4px;
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: white;
  }
`;
