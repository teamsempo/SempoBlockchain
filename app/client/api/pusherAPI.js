import { startConfiguration } from 'pusher-redux';
import { generateFormattedURL, getToken } from '../utils';

export const authenticatePusher = () => {
  startConfiguration({
    auth: {
      headers: {
        Authorization: getToken(),
      },
    },
    authEndpoint: generateFormattedURL('/pusher/auth'),
  });
};
