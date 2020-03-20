import React from 'react';
import { connect } from 'react-redux';
import styled from 'styled-components';

class hideableDiv extends React.Component {
  constructor() {
    super();
    this.state = {
      isHidden: false,
    };
  }

  toggleHidden() {
    // this.setState({
    //   isHidden: !this.state.isHidden
    // })
  }

  render() {
    return (
      <WrapperDiv>
        <Title onClick={this.toggleHidden.bind(this)}>
          <div style={{ display: 'flex' }}>
            <h2>{this.props.title}</h2>
            {/* <IconSVG src={this.state.isHidden ? '/static/media/cross.svg' : '/static/media/angle-down.svg'} /> */}
          </div>
        </Title>
        {this.state.isHidden && (
          <ExpandableText>{this.props.children}</ExpandableText>
        )}
      </WrapperDiv>
    );
  }
}

export default hideableDiv;

const WrapperDiv = styled.div`
  width: 100%;
`;

const Title = styled.button`
  //background: #6a7680;
  background: #ebf0f5;
  border-radius: 0.2rem;
  text-transform: uppercase;
  transition: all 0.15s ease;
  text-align: left;
  color: #4a4a4a;
  width: calc(100% - 2em);
  margin: 1em;
  overflow: hidden;
  position: relative;
  border: none;
  padding: 0 1em;
  &:focus {
    outline: none;
  }
`;

const ExpandableText = styled.div`
  margin: 0 2.5em 1em;
`;

const IconSVG = styled.img`
  height: 2em;
  margin: auto 1em;
`;
