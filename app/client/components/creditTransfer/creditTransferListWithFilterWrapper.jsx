import React from "react";
import styled from "styled-components";

import CreditTransferList from "./LegacyCreditTransferList.jsx";
import SearchBoxWithFilter from "../filterModule/SearchBoxWithFilter.jsx";

export default class CreditTransferListWithFilterWrapper extends React.Component {
  constructor() {
    super();
    this.state = {};

    this.searchKeys = [
      "transfer_amount",
      "created",
      "transfer_status",
      "transfer_type",
      "id",
      "transfer_use",
      "recipient",
      "sender"
    ];

    this.filterKeys = {
      transfer_amount: amount => amount / 100,
      created: null,
      transfer_status: null,
      transfer_type: null,
      transfer_use: null
    };
  }

  render() {
    var item_list = this.props.creditTransferList.sort((a, b) => b.id - a.id);

    return (
      <Wrapper>
        <SearchBoxWithFilter
          item_list={item_list}
          searchKeys={this.searchKeys}
          filterKeys={this.filterKeys}
        >
          <CreditTransferList />
        </SearchBoxWithFilter>
      </Wrapper>
    );
  }
}

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
`;
