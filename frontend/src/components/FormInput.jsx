import React from "react";

const FormInput = ({ label, ...props }) => (
  <div className="mb-4">
    <label className="block text-sm font-medium mb-1">{label}</label>
    <input className="w-full border rounded px-3 py-2" {...props} />
  </div>
);

export default FormInput;
