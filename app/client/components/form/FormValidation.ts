import { parsePhoneNumberFromString } from "libphonenumber-js";

const FormValidation = {
  required: (value: string | number) =>
    value !== undefined && value !== "" ? undefined : "This field is required",
  phone: (value: string) => {
    if (value) {
      let formattedNumber = value.split(" ");
      if (formattedNumber.length === 1) {
        return undefined;
      }
      const number = parsePhoneNumberFromString(value);
      if (number && number.isValid()) {
        return undefined;
      } else {
        return "Please enter a proper phone number";
      }
    }
  },
  antPhone: async (value: string) => {
    if (value) {
      if (value.length === 1) {
        return Promise.reject(new Error("Please enter a proper phone number"));
      }
      const formattedNumber = value.includes("+") ? value : "+" + value;
      const number = parsePhoneNumberFromString(formattedNumber);
      if (number && number.isValid()) {
        return Promise.resolve();
      } else {
        return Promise.reject(new Error("Please enter a proper phone number"));
      }
    }
  },
  notOther: (value: string) =>
    value.toLowerCase() === "other"
      ? "'Other' is not a valid input"
      : undefined,
  isNumber: (value: number) => (isNaN(value) ? "Must be a number" : undefined)
};

export default FormValidation;
