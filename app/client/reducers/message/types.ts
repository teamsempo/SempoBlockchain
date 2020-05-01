export enum MessageActionTypes {
  ADD_FLASH_MESSAGE = "ADD_FLASH_MESSAGE",
  SHOW_FLASH = "SHOW_FLASH",
  CLEAR_FLASH = "CLEAR_FLASH"
}

export interface AddMessagePayload {
  error: boolean;
  message: string;
}
