import styled from "styled-components";
import { Link } from "react-router-dom";

export const PageWrapper = styled.div`
  width: 100%;
  @media (max-width: 767px) {
    margin-left: 0;
    width: 100%;
    flex-direction: column;
  }
`;

export const CenterLoadingSideBarActive = styled.div`
  width: 100%;
  flex-direction: column;
  height: 100vh;
  display: flex;
  justify-content: center;
  @media (max-width: 767px) {
    margin-left: 0;
    width: 100%;
  }
`;

export const Input = styled.input`
  width: calc(100% - 1em);
  outline: none;
  display: flex;
  margin: 0.5em;
  padding: 0.5em;
  border: 1px solid rgba(0, 0, 0, 0.15);
  background-color: #fff;
  background-image: none;
  background-clip: padding-box;
  font-size: 1em;
  font-weight: 200;
  color: #495057;
  transition: all 0.25s cubic-bezier(0.25, 0.8, 0.25, 1);
  &:focus {
    border-color: #34b0b3;
  }
`;

export const ModuleBox = styled.div`
  margin: 1em;
  background-color: #fff;
  box-shadow: 0px 2px 0px 0 rgba(51, 51, 79, 0.08);
  overflow: hidden;
  position: relative;
`;

export const RestrictedModuleBox = styled(ModuleBox)`
    width: 50%;
    @media (max-width: 767px) {
    width: 100%;
`;

// export const StyledButton = styled.button`
//   margin: 0.5em;
//   padding: 0.5em;
//   border-radius: .2rem;
//   font-size: 1em;
//   font-weight: 200;
//   color: #495057;
// `;

export const StyledButton = styled.button`
  outline: none;
  border: 0;
  white-space: nowrap;
  display: inline-block;
  height: 40px;
  line-height: 40px;
  padding: 0 14px;
  margin: 0.5em;
  box-shadow: 0px 2px 0px 0 rgba(51, 51, 79, 0.08);
  background: ${props => props.theme.background};
  font-size: 1em;
  font-weight: 200;
  text-transform: uppercase;
  -webkit-letter-spacing: 0.025em;
  -moz-letter-spacing: 0.025em;
  -ms-letter-spacing: 0.025em;
  letter-spacing: 0.025em;
  color: ${props => props.theme.color};
  text-decoration: none;
  -webkit-transition: all 0.15s ease;
  transition: all 0.15s ease;
  cursor: pointer;
  &:hover {
    background-color: ${props => props.theme.backgroundColor};
  }
`;

export const StyledSelect = styled.select`
  //-webkit-appearance: none;
  // border-radius: 0;
  outline: none;
  border: 0;
  white-space: nowrap;
  display: inline-block;
  height: 40px;
  line-height: 40px;
  padding: 0 14px;
  margin: 0.5em;
  box-shadow: 0px 2px 0px 0 rgba(51, 51, 79, 0.08);
  background: ${props => props.theme.background};
  font-size: 1em;
  font-weight: 200;
  text-transform: uppercase;
  -webkit-letter-spacing: 0.025em;
  -moz-letter-spacing: 0.025em;
  -ms-letter-spacing: 0.025em;
  letter-spacing: 0.025em;
  color: ${props => props.theme.color};
  text-decoration: none;
  -webkit-transition: all 0.15s ease;
  transition: all 0.15s ease;
  &:hover {
    //background-color: #34b0b3;
    background-color: ${props => props.theme.backgroundColor};
  }
`;

export const PlainTextButton = styled.button`
  margin: 0.5em;
  padding: 0.5em;
  font-size: 0.8em;
  font-weight: 200;
  color: #495057;
  border: none;
`;

export const ErrorMessage = styled.div`
  height: 1.2em;
  color: #ff715b;
  margin: 0.5em;
`;

export const ModuleHeader = styled.h1`
  text-transform: uppercase;
  position: relative;
  margin: 0;
  padding: 1em;
  top: 0;
  text-align: center;
  width: auto;
  background-color: #fff;
  font-size: 15px;
  color: #4e575e;
  font-weight: 600;
  letter-spacing: 1px;
`;

export const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
`;

export const TopRow = styled.div`
  display: flex;
  width: 100%;
  justify-content: space-between;
  align-items: center;
  @media (max-width: 767px) {
    min-width: fit-content;
  }
`;

export const Row = styled.div`
  display: flex;
  flex-direction: row;
  width: 100%;
  @media (max-width: 767px) {
    flex-direction: column;
    width: calc(100% - 2em);
  }
`;

export const SubRow = styled.div`
  display: flex;
  align-items: center;
  width: 33%;
  @media (max-width: 767px) {
    width: 100%;
    justify-content: space-between;
  }
`;

export const InputObject = styled.label`
  display: block;
  padding: 1em;
  font-size: 15px;
`;

export const InputLabel = styled.div`
  display: block;
  font-size: 14px;
`;

export const WrapperDiv = styled.div`
  display: flex;
  justify-content: center;
  align-items: center;
  flex-direction: column;
  position: relative;
`;

export const Modal = styled.div`
  //display: none; /* Hidden by default */
  position: fixed; /* Stay in place */
  z-index: 1000; /* Sit on top */
  left: 0;
  top: 0;
  width: 100%; /* Full width */
  height: 100%; /* Full height */
  overflow: auto; /* Enable scroll if needed */
  background-color: rgb(0, 0, 0); /* Fallback color */
  background-color: rgba(0, 0, 0, 0.4); /* Black w/ opacity */
`;

export const ModalContent = styled.div`
  background-color: #fefefe;
  margin: 15% auto; /* 15% from the top and centered */
  padding: 20px;
  border: 1px solid #888;
  width: 80%; /* Could be more or less, depending on screen size */
`;

export const ModalClose = styled.img`
  color: #aaa;
  float: right;
  font-size: 28px;
  font-weight: bold;
  height: 20px;
`;

export const FooterBar = styled.div`
  display: flex;
  border-top: solid 1px rgba(0, 0, 0, 0.05);
  padding: 1em;
`;

export const ButtonWrapper = styled.div`
  margin: auto 1em;
  @media (max-width: 767px) {
    margin: auto 1em;
    display: flex;
    flex-direction: column;
  }
`;
