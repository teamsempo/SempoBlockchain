import React from 'react'

export default class StepWizard extends React.Component {
  render() {
    let { steps, activeStep } = this.props;

    // generate header
    let header = <ol className='progtrckr'>{steps.map((step, idx) => {
      return (
        <li className={'progtrckr-' + (idx === activeStep ? 'doing' : idx > activeStep ? 'todo' : 'done') + ' no-hl'} key={idx}><em>{idx}</em><span>{step.name}</span></li>
      )
    })}</ol>;

    // return active component
    let activeComponent = steps[activeStep].component;

    // return footer

    return(
      <div className='step-progress'>
        <div className='multi-step'>
          {header}
          {activeComponent}
        </div>
      </div>
    )
  }
}