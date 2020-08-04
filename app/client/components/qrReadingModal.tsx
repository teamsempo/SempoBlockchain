import React, { Suspense, lazy, useState } from "react";
const QrReader = lazy(() => import("react-qr-reader"));
import { Modal, ModalContent, ModalClose } from "./styledElements";

interface Props {
  updateData: (any: any) => any;
}
export default function QrReadingModal(props: Props) {
  const [existingQrData, setExistingQrData] = useState<any | null>(null);
  const [readerActive, setReaderActive] = useState(false);

  function handleScan(data: any) {
    if (data && data !== existingQrData) {
      setReaderActive(false);
      props.updateData(data);
    }
  }

  function handleError(err: any) {
    console.error(err);
  }

  function toggleModal() {
    setReaderActive(!readerActive);
  }

  let qrReader;
  if (readerActive) {
    qrReader = (
      <Modal onClick={() => toggleModal()}>
        <ModalContent style={{ maxWidth: "300px" }}>
          <ModalClose src={"/static/media/cross.svg"} />
          <h4 style={{ marginTop: "0em", marginLeft: "0em" }}>
            Scan an ID card's QR code.
          </h4>
          <Suspense fallback={<div>Loading QR Reader...</div>}>
            <QrReader
              delay={300}
              onError={handleError}
              onScan={handleScan}
              style={{ width: "100%" }}
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
          margin: "0.2em",
          width: "1.4em",
          height: "1.4em"
        }}
        onClick={() => toggleModal()}
      >
        <img style={{ width: "100%" }} src={"/static/media/qrCodeIcon.svg"} />
      </div>
      {qrReader}
    </div>
  );
}
