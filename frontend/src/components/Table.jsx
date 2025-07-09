import React from "react";

const Table = ({ columns, data }) => (
  <table className="min-w-full border">
    <thead>
      <tr>
        {columns.map(col => (
          <th key={col.key} className="px-4 py-2 border-b bg-gray-100 text-left">{col.label}</th>
        ))}
      </tr>
    </thead>
    <tbody>
      {data.map((row, i) => (
        <tr key={i}>
          {columns.map(col => (
            <td key={col.key} className="px-4 py-2 border-b">{row[col.key]}</td>
          ))}
        </tr>
      ))}
    </tbody>
  </table>
);

export default Table;
