import React from 'react';
import { connect } from 'react-redux';

import {Organisation} from "../../reducers/organisation/types";
import SideBar from "../navBar";
import styles from "./Page.module.css";
import OrganisationSettingForm, {IOrganisationSettings} from "../organisation/OrganisationSettingForm";

interface StateProps {
  organisations: Organisation[]
}

class OrganisationPage extends React.Component<StateProps> {
  onSubmit(form: IOrganisationSettings) {
    //TODO(org): update settings
  }

  render() {
    return <div className={styles.wrapper}>
      <SideBar/>

      <div className={styles.pageWrapper}>
        <div>Organisation Settings</div>
        <OrganisationSettingForm onSubmit={(form) => this.onSubmit(form)}/>
      </div>
    </div>
  }
}

const mapStateToProps = (state: any) => {
  return {
    organisations: state.organisations.organisations
  };
};

const mapDispatchToProps = (dispatch: any) => {
  return {
  };
};

export default connect(mapStateToProps, mapDispatchToProps)(OrganisationPage);