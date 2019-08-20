import { getToken, handleResponse } from '../utils'

//Request QR Code API Call
export const qrCodeCheckAPI = (qr_data, transfer_amount) => {
  return fetch('/api/qr_check/', {
    headers: {
      'Authorization': getToken(),
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    method: 'POST',
    body: JSON.stringify({'qr_data': qr_data, 'transfer_amount': transfer_amount})
  }).then(response => {
      return handleResponse(response)
  }).catch(error => {
      throw error;
  })
};

//Confirm QR Code Transaction API Call
export const qrCodeTransferAPI = (qr_data, transfer_amount, pin) => {
  return fetch('/api/qr_transfer/', {
    headers: {
      'Authorization': getToken(),
      'Accept': 'application/json',
      'Content-Type': 'application/json'
    },
    method: 'POST',
    body: JSON.stringify({'qr_data': qr_data, 'transfer_amount': transfer_amount, 'pin': pin})
  }).then(response => {
      return handleResponse(response)
  }).catch(error => {
      throw error;
  })
};