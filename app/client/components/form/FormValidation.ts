import { parsePhoneNumberFromString } from 'libphonenumber-js';

const FormValidation = {
  required: (value: string | number) =>
    value !== undefined && value !== '' ? undefined : 'This field is required',
  phone: (value: string) => {
    if (value) {
      //TODO(org): set default country here, currently requires to be full number with +country code
      const number = parsePhoneNumberFromString(value);
      if (number && number.isValid()) {
        return undefined;
      } else {
        return 'Please enter a proper phone number';
      }
    }
  },
  notOther: (value: string) =>
    value.toLowerCase() === 'other'
      ? "'Other' is not a valid input"
      : undefined,
  isNumber: (value: number) => (isNaN(value) ? 'Must be a number' : undefined),
};

export default FormValidation;
