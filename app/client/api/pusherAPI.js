import { generateFormattedURL, getToken } from "../utils";
import { startConfiguration } from 'pusher-redux';

export const authenticatePusher = () => {
  startConfiguration({
    auth: {
      headers: {
        'Authorization': getToken()
      }
    },
    authEndpoint: generateFormattedURL('/pusher/auth')
  });
};
