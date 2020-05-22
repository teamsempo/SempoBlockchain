import { generateFormattedURLPath, getToken } from "../utils";
import { startConfiguration } from "pusher-redux";

export const authenticatePusher = () => {
  startConfiguration({
    auth: {
      headers: {
        Authorization: getToken()
      }
    },
    authEndpoint: generateFormattedURLPath("/pusher/auth")
  });
};
