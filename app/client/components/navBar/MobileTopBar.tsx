import * as React from "react";
import styled from "styled-components";
import { SVG, StyledLogoLink } from "./styles";

interface Props {
  iconUrl: string;
  email: string | null;
  menuOpen: boolean;
  onPress: () => any;
}

const MobileTopBar: React.FunctionComponent<Props> = ({
  iconUrl,
  email,
  menuOpen,
  onPress
}) => {
  return (
    <MobileTopBarContainer>
      <StyledLogoLink to="/">
        <SVG src={iconUrl} />
      </StyledLogoLink>
      <Title>{email}</Title>
      <MenuContainer onClick={onPress}>
        {menuOpen ? (
          <SVG src="/static/media/close.svg" />
        ) : (
          <SVG src="/static/media/stack.svg" />
        )}
      </MenuContainer>
    </MobileTopBarContainer>
  );
};

export default MobileTopBar;

const MobileTopBarContainer = styled.div`
  width: inherit;
  display: flex;
  justify-content: space-between;
  height: 50px;
`;

const MenuContainer = styled.p`
  margin: auto 1em;
  color: #fff;
`;

const Title = styled.h2`
  color: #fff;
  margin: auto 1em;
  font-size: 22px;
  font-weight: 600;
  text-decoration: none;
  letter-spacing: 1.5px;
  @media (max-width: 767px) {
    overflow: hidden;
    text-overflow: ellipsis;
    font-size: 16px;
    line-height: 1;
    text-align: center;
  }
`;
