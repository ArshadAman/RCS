import React from "react";

const Pagination = ({ page, totalPages, onPageChange }) => {
  if (totalPages <= 1) return null;
  return (
    <div className="flex justify-center mt-4">
      <button
        className="px-3 py-1 mx-1 bg-gray-200 rounded disabled:opacity-50"
        onClick={() => onPageChange(page - 1)}
        disabled={page === 1}
      >
        Prev
      </button>
      <span className="px-3 py-1 mx-1">{page} / {totalPages}</span>
      <button
        className="px-3 py-1 mx-1 bg-gray-200 rounded disabled:opacity-50"
        onClick={() => onPageChange(page + 1)}
        disabled={page === totalPages}
      >
        Next
      </button>
    </div>
  );
};

export default Pagination;
