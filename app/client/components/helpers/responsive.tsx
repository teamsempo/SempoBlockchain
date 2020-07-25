import * as React from "react";
import MediaQuery, { useMediaQuery } from "react-responsive";

type Props = {
  children: React.ReactNode;
};

export const Mobile: React.FunctionComponent<Props> = ({
  children
}: {
  children: React.ReactNode;
}) => {
  return <MediaQuery maxWidth={767}>{children}</MediaQuery>;
};

export const isMobile = () => {
  return useMediaQuery({ query: "(max-width: 767px)" });
};

export const Default: React.FunctionComponent<Props> = ({
  children
}: {
  children: React.ReactNode;
}) => {
  return <MediaQuery minWidth={768}>{children}</MediaQuery>;
};
