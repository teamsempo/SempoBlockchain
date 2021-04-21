import React from "react";
import * as Sentry from "@sentry/browser";

interface Props {
  noNav?: boolean;
  children?: React.ReactNode;
}

interface State {
  error: boolean | null;
}

export default class ErrorBoundary extends React.Component<Props, State> {
  constructor(props: any) {
    super(props);
    this.state = { error: null };
  }

  componentDidCatch(error: any, errorInfo: any) {
    console.log(error);
    console.log(errorInfo);

    this.setState({ error });
    Sentry.withScope(scope => {
      Object.keys(errorInfo).forEach(key => {
        scope.setExtra(key, errorInfo[key]);
      });
      Sentry.captureException(error);
    });
  }

  render() {
    if (this.state.error) {
      // You can render any custom fallback UI
      let style = this.props.noNav
        ? { width: "calc(100% - 234px)", marginLeft: "234px" }
        : undefined;
      return (
        <div style={style}>
          <h1>Something went wrong.</h1>
          <a onClick={() => Sentry.showReportDialog()}>Report feedback</a>
        </div>
      );
    }
    return this.props.children;
  }
}
