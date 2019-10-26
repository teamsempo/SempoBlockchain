const FormValidation = {
  required: (value: string | number) => (value !== undefined && value !== "") ? undefined : "This field is required"
};

export default FormValidation;