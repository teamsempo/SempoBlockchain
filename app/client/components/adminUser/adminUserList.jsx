import React from 'react';
import { connect } from 'react-redux';
import { browserHistory } from "../../app.jsx";

import styled from 'styled-components';
import ReactTable from 'react-table'

import { TopRow, StyledButton, ModuleHeader } from '../styledElements.js'

import { loadUserList, updateUser } from '../../reducers/auth/actions'
import LoadingSpinner from "../loadingSpinner.jsx";

const mapStateToProps = (state) => {
  return {
  	login: state.login,
    loggedIn: (state.login.userId != null),
		adminUsers: state.adminUsers,
		adminUserList: Object.keys(state.adminUsers.byId).map(id => state.adminUsers.byId[id]),
		updateUserRequest: state.updateUserRequest,
  };
};

const mapDispatchToProps = (dispatch) => {
  return {
    loadUserList: () => dispatch(loadUserList()),
    updateUser: (body, query) => dispatch(updateUser({body, query}))
  };
};

class AdminUserList extends React.Component {
  constructor() {
	super();
	this.state = {
	  data: [],
	  pages: null,
	  loading: true,
	  action: false,
	  user_id: null,
	};
  }

  componentDidMount() {
  	this.props.loadUserList()
  }

  updateUserAccountPermissions(user_id, admin_tier, deactivated) {
  	this.props.updateUser(
  		{
			user_id: user_id,
			admin_tier: admin_tier,
			deactivated: deactivated},
			{

			}
			)
  }


  displayCorrectStatus(id) {
	  if (this.props.adminUserList.find(x => x.id === id).is_disabled) {
	  	var StatusComponent =
			  <StatusWrapper>
				  <DisabledIcon style={{backgroundColor: 'rgba(255, 0, 0, 0.8)'}}>Disabled</DisabledIcon>
			  </StatusWrapper>

      } else if (!this.props.adminUserList.find(x => x.id === id).is_activated) {
	  	StatusComponent =
			  <StatusWrapper>
				  <DisabledIcon style={{backgroundColor: 'rgba(39, 164, 167, 0.8)'}}>Unactivated</DisabledIcon>
			  </StatusWrapper>
	  }
	  return StatusComponent
  }

  displayActionItems(id) {
  	let default_action_items = [
  		{'query': 'superadmin', 'display': 'Change to Super Admin', 'deactivated': null},
      {'query': 'admin', 'display': 'Change to Admin', 'deactivated': null},
      {'query': 'subadmin', 'display': 'Change to Enroller', 'deactivated': null},
      {'query': 'view', 'display': 'Change to View Only', 'deactivated': null}
    ];

	if (this.props.adminUserList.find(x => x.id === id).is_disabled) {
		var formatted_action_item = {'query': null, 'display': 'Enable User', 'deactivated': false};
		default_action_items.push(formatted_action_item);
	} else {
  		formatted_action_item = {'query': null, 'display': 'Disable User', 'deactivated': true};
  		default_action_items.push(formatted_action_item);
	}

  	if (this.state.action) {
		return(
		 default_action_items.map(item => <ActionItem style={{color: (item.deactivated === false ? '#30a4a6' : ''), width: '100%'}} key={item.query} onClick={() => this.setState({action: !this.state.action, user_id: null}, this.updateUserAccountPermissions(id, item.query, item.deactivated))}>{item.display}</ActionItem>)
		)
	}
  }

  displayActionComponent(id) {
  	const isSelected = this.state.user_id === id;

  	if (isSelected) {
  		var ActionItems =
			<ActionWrapper
				  style={{display: (this.state.user_id === id ? '' : 'none')}}>
				{this.displayActionItems(id)}
	  		</ActionWrapper>
	} else {
  		ActionItems = null;
	}

	return(
		<div>
		  <IconWrapper style={{border: (this.state.user_id === id ? 'solid 1px rgba(0,0,0,0.05)' : '')}} onClick={() => this.setState({
			  action: !this.state.action,
			  user_id: id
		  })}>
			  <IconSVG src="/static/media/action-icon.svg"/>
		  </IconWrapper>
		  <CloseWrapper
			  onClick={() => this.setState({action: !this.state.action, user_id: null})}
			  style={{display: (this.state.action ? '' : 'none')}}/>
			{ActionItems}
		</div>
	)
  }

  render() {
  	const { adminUsers, adminUserList } = this.props;
	  const loadingStatus = adminUsers.loadStatus.isRequesting || adminUsers.createStatus.isRequesting;

	  if (loadingStatus) {
	    return (
	      <div style={{justifyContent: 'center', display: 'flex', padding: '10vh 10vw'}}>
			    <LoadingSpinner />
		    </div>
      )
    }

	  if (adminUsers.loadStatus.success) {
		  const tableLength = adminUserList.length;
		  const sortedUserList = adminUserList.sort((a, b) => (a.id - b.id));

		  return (
			  <Wrapper>
				  <TopRow>
					  <ModuleHeader>USERS</ModuleHeader>
						<div>
							<UploadButtonWrapper style={{marginRight: 0, marginLeft: 0}}>
								<StyledButton onClick={() => browserHistory.push('/settings/invite')} style={{fontWeight: '400', margin: '0em 1em', lineHeight: '25px', height: '25px'}}>
								+ New User
								</StyledButton>
							</UploadButtonWrapper>
						</div>
				  </TopRow>
				  <ReactTable
					  columns={[
              {
                Header: "Name",
                accessor: "email",
                headerClassName: 'react-table-header',
                className: 'react-table-first-cell'
              },
              {
                Header: "Account Type",
                accessor: "admin_tier",
                headerClassName: 'react-table-header',
              },
              {
                Header: "Created",
                accessor: "created",
                headerClassName: 'react-table-header',
              },
						  {
                Header: "Status",
                accessor: "id",
                headerClassName: 'react-table-header',
							  Cell: cellInfo => this.displayCorrectStatus(cellInfo.value)
              },
              {
                Header: "",
                accessor: "id",
                headerClassName: 'react-table-header',
                width: 60,
                Cell: cellInfo => this.displayActionComponent(cellInfo.value)
              }
            ]}
					  data={sortedUserList}
					  loading={loadingStatus} // Display the loading overlay when we need it
					  defaultPageSize={tableLength}
					  sortable={false}
					  showPagination={false}
					  showPageSizeOptions={false}
					  className='react-table'
					  resizable={false}
				  />
				  <FooterBar>
					  <p style={{margin: 0}}>{tableLength} users</p>
				  </FooterBar>
			  </Wrapper>
      );
	  }

	  if (this.props.login.adminTier === 'view' || this.props.login.adminTier === 'subadmin') {
	    return(
        <div style={{justifyContent: 'center', display: 'flex', padding: '10vh 10vw'}}>
          <p>You don't have access to admin list.</p>
        </div>
      )
    }

	  return(
	  	<div style={{justifyContent: 'center', display: 'flex', padding: '10vh 10vw'}}>
			  <p>Something went wrong.</p>
      </div>
	  )
  }
};

export default connect(mapStateToProps, mapDispatchToProps)(AdminUserList);

const StatusWrapper = styled.div`
    display: flex;
`;

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
`;

const DisabledIcon = styled.p`
    color: #FFF;
    padding: 0.2em 1em;
    margin: 0;
    font-weight: 500;
    border-radius: 20px;
    text-transform: uppercase;
    font-size: 12px;
`;

const UploadButtonWrapper = styled.div`
  margin: auto 1em;
`;

const CloseWrapper = styled.div`
	position: fixed;
	top: 0;
	left: 0;
	background-color: transparent;
	z-index: 501;
	width: 100vw;
	height: 100vh;
`;

const ActionWrapper = styled.div`
	right: calc(1em + 5px);
	position: absolute;
    margin-left: -11em;
    background-color: #fff;
    box-shadow: 0 0 0 1px rgba(44,45,48,.15), 0 5px 10px rgba(44,45,48,.12);
    padding: 1em 0;
    user-select: none;
    width: 200px;
    z-index: 502;
    margin-bottom: 1em;
`;

const ActionItem = styled.div`
    width: 100%;
    padding: 0.5em 1em;
    margin: 0;
    font-weight: 400;
    :hover {
    background-color: #f7fafc;
    };
    :last-child {
    border-top: solid 1px rgba(0,0,0,0.05);
    margin-top: 0.5em;
    color: red;
    }
`;

const IconWrapper = styled.span`
	border: solid 1px rgba(0,0,0,0);
	border-radius: 5px;
    padding: 1px;
    :hover {
    border: solid 1px rgba(0,0,0,0.05);
    }
`;

const IconSVG = styled.img`
  margin-top: auto;
  margin-bottom: auto;
  width: 22px;
`;

const FooterBar = styled.div`
    border-top: solid 1px rgba(0,0,0,0.05);
    padding: 1em;
`;
