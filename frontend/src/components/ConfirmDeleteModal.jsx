import React from "react";

const ConfirmDeleteModal = ({ isOpen, onClose, onConfirm, message }) => {
  if (!isOpen) return null;
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-black bg-opacity-40 z-50">
      <div className="bg-white p-6 rounded shadow w-full max-w-sm">
        <h2 className="text-xl font-bold mb-4">Confirm Delete</h2>
        <p className="mb-6">{message || "Are you sure you want to delete this item?"}</p>
        <div className="flex justify-end">
          <button className="mr-2 px-4 py-2 bg-gray-200 rounded" onClick={onClose}>Cancel</button>
          <button className="px-4 py-2 bg-red-600 text-white rounded" onClick={onConfirm}>Delete</button>
        </div>
      </div>
    </div>
  );
};

export default ConfirmDeleteModal;
