export const QR_CODE_REQUEST = 'QR_CODE_REQUEST';
export const QR_CODE_SUCCESS = 'QR_CODE_SUCCESS';
export const QR_CODE_FAILURE = 'QR_CODE_FAILURE';

export const QR_CODE_TRANSFER_REQUEST = 'QR_CODE_TRANSFER_REQUEST';
export const QR_CODE_TRANSFER_SUCCESS = 'QR_CODE_TRANSFER_SUCCESS';
export const QR_CODE_TRANSFER_FAILURE = 'QR_CODE_TRANSFER_FAILURE';

export const initialQrCodeCheckState = {
  isRequesting: false,
  loaded: false,
  data: {first_name: null, last_name: null, sufficient_funds: null},
  error: null
};

export const qrCodeCheck = (state = initialQrCodeCheckState, action) => {
  switch (action.type) {
    case QR_CODE_REQUEST:
      return {...state, isRequesting: true, error: null, loaded: false};
    case QR_CODE_SUCCESS:
      return {...state, isRequesting: false, data: action.result.data, loaded: true};
    case QR_CODE_FAILURE:
      return {...state, isRequesting: false, error: action.error || 'unknown error'};
    default:
      return state;
  }
};

export const initialQrCodeTransferState = {
  isRequesting: false,
  success: false,
  error: null
};

export const qrCodeTransfer = (state = initialQrCodeTransferState, action) => {
  switch (action.type) {
    case QR_CODE_TRANSFER_REQUEST:
      return {...state, isRequesting: true, error: null, success: false};
    case QR_CODE_TRANSFER_SUCCESS:
      return {...state, isRequesting: false, success: true};
    case QR_CODE_TRANSFER_FAILURE:
      return {...state, isRequesting: false, error: action.error || 'unknown error'};
    default:
      return state;
  }
};


// Actions

export const checkQrCode = ({qr_data, transfer_amount}) => (
  {
    type: QR_CODE_REQUEST,
    qr_data,
    transfer_amount
  }
);

export const transferQrCode = ({qr_data, transfer_amount, pin}) => (
  {
    type: QR_CODE_TRANSFER_REQUEST,
    qr_data,
    transfer_amount,
    pin
  }
);