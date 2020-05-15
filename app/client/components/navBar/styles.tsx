import styled from "styled-components";
import { NavLink } from "react-router-dom";

export const SVG = styled.img`
  width: 35px;
  padding: 1em 0;
  display: flex;
  @media (max-width: 767px) {
    padding: 0;
    width: 30px;
  }
`;

export const StyledLogoLink = styled(NavLink)`
  color: #fff;
  margin: auto 1em;
  font-size: 22px;
  font-weight: 600;
  text-decoration: none;
  letter-spacing: 1.5px;
  @media (max-width: 767px) {
    margin: auto 0.5em;
  }
`;
