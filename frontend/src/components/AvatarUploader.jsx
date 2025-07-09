import React from "react";

const AvatarUploader = ({ value, onChange }) => {
  return (
    <div className="mb-4">
      <label className="block text-sm font-medium mb-1">Avatar</label>
      <input type="file" accept="image/*" onChange={onChange} />
      {value && (
        <img src={typeof value === 'string' ? value : URL.createObjectURL(value)} alt="avatar" className="mt-2 w-16 h-16 rounded-full object-cover" />
      )}
    </div>
  );
};

export default AvatarUploader;
