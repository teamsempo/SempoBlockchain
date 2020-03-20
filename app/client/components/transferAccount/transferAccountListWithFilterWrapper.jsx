import React from 'react';
import styled from 'styled-components';

import TransferAccountList from './transferAccountList.jsx';
import SearchBoxWithFilter from '../SearchBoxWithFilter.jsx';

export default class TransferAccountListWithFilterWrapper extends React.Component {
  constructor() {
    super();
    this.state = {};

    this.searchKeys = [
      'balance',
      'created',
      'first_name',
      'last_name',
      'id',
      'is_approved',
      'phone',
      'public_serial_number',
    ];

    this.filterKeys = {
      balance: amount => amount / 100,
      created: null,
      is_approved: null,
      location: null,
    };
  }

  render() {
    const item_list = this.props.transferAccountList.sort(
      (a, b) => b.id - a.id,
    );

    return (
      <Wrapper>
        <SearchBoxWithFilter
          item_list={item_list}
          searchKeys={this.searchKeys}
          filterKeys={this.filterKeys}>
          <TransferAccountList />
        </SearchBoxWithFilter>
      </Wrapper>
    );
  }
}

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
`;
