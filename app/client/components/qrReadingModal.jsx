import React, { Suspense, lazy } from 'react';
const QrReader = lazy(() => import('react-qr-reader'));

// import QrReader from 'react-qr-reader'

import { Modal, ModalContent, ModalClose } from './styledElements';

export default class QrReadingModal extends React.Component {
  constructor() {
    super();

    this.state = {
      existingQrData: null,
      readerActive: false,
    };
  }

  handleScan = data => {
    if (data && data !== this.state.existingQrData) {
      this.setState(
        {
          // existingQrData: data
          readerActive: false,
        },
        this.props.updateData(data),
      );
    }
  };

  handleError = err => {
    console.error(err);
  };

  toggleModal = () => {
    this.setState({
      readerActive: !this.state.readerActive,
    });
  };

  render() {
    if (this.state.readerActive) {
      var qrReader = (
        <Modal onClick={() => this.toggleModal()}>
          <ModalContent style={{ maxWidth: '300px' }}>
            <ModalClose src={'/static/media/cross.svg'} />
            <h4 style={{ marginTop: '0em', marginLeft: '0em' }}>
              Scan an ID card's QR code.
            </h4>
            <Suspense fallback={<div>Loading QR Reader...</div>}>
              <QrReader
                delay={300}
                onError={this.handleError}
                onScan={this.handleScan}
                style={{ width: '100%' }}
              />
            </Suspense>
          </ModalContent>
        </Modal>
      );
    } else {
      qrReader = null;
    }

    return (
      <div>
        <div
          style={{
            margin: '0.2em',
            width: '1.4em',
            height: '1.4em',
          }}
          onClick={() => this.toggleModal()}>
          <img style={{ width: '100%' }} src={'/static/media/qrCodeIcon.svg'} />
        </div>
        {qrReader}
      </div>
    );
  }
}
