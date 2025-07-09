import React from "react";

const FormError = ({ error }) => (
  error ? <div className="text-red-600 text-sm mb-2">{error}</div> : null
);

export default FormError;
