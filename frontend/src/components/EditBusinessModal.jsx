import React from "react";

const EditBusinessModal = ({ isOpen, onClose, onSave, business }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-40 z-50">
      <div className="bg-white p-6 rounded shadow w-full max-w-md">
        <h2 className="text-xl font-bold mb-4">Edit Business</h2>
        {/* TODO: Add business edit form, prefill with business data */}
        <div className="flex justify-end mt-4">
          <button className="mr-2 px-4 py-2 bg-gray-200 rounded" onClick={onClose}>Cancel</button>
          <button className="px-4 py-2 bg-blue-600 text-white rounded" onClick={onSave}>Save</button>
        </div>
      </div>
    </div>
  );
};

export default EditBusinessModal;
