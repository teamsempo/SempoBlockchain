import React from 'react';

export default class StepWizard extends React.Component {
  render() {
    const { steps, activeStep } = this.props;

    // generate header
    const header = (
      <ol className="progtrckr">
        {steps.map((step, idx) => (
          <li
            className={`progtrckr-${
              idx === activeStep ? 'doing' : idx > activeStep ? 'todo' : 'done'
            } no-hl`}
            key={idx}>
            <em>{idx}</em>
            <span>{step.name}</span>
          </li>
        ))}
      </ol>
    );

    // return active component
    const activeComponent = steps[activeStep].component;

    // return footer

    return (
      <div className="step-progress">
        <div className="multi-step">
          {header}
          {activeComponent}
        </div>
      </div>
    );
  }
}
