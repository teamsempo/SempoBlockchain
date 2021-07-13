import React, { Suspense, lazy, useState } from "react";
const QrReader = lazy(() => import("react-qr-reader"));
import { Modal, Button, Tooltip } from "antd";
import { QrcodeOutlined } from "@ant-design/icons";

interface Props {
  updateData: (any: any) => any;
  disabled?: boolean;
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

  return (
    <div>
      <Tooltip title="Scan QR Code">
        <Button
          disabled={props.disabled}
          onClick={toggleModal}
          icon={<QrcodeOutlined translate={""} />}
          type="link"
          size={"small"}
        />
      </Tooltip>
      <Modal
        title="Scan an ID card's QR code"
        visible={readerActive}
        onOk={toggleModal}
        onCancel={toggleModal}
        style={{ maxWidth: "400px" }}
      >
        <Suspense fallback={<div>Loading QR Reader...</div>}>
          <QrReader
            delay={300}
            onError={handleError}
            onScan={handleScan}
            style={{ width: "100%" }}
          />
        </Suspense>
      </Modal>
    </div>
  );
}
