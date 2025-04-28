 // frontend/src/components/Results/DataTable.js
import React from 'react';

const DataTable = ({ columns, data }) => {
  if (!data || data.length === 0) {
    return <p className="text-center text-gray-500 italic my-4">No data to display.</p>;
  }

  // Ensure columns are provided, otherwise derive from first data row
  const headerColumns = columns && columns.length > 0 ? columns : Object.keys(data[0]);

  return (
    <div className="overflow-x-auto my-4 shadow rounded-lg border border-gray-200">
      <table className="min-w-full divide-y divide-gray-200">
        <thead className="bg-gray-50">
          <tr>
            {headerColumns.map((col) => (
              <th
                key={col}
                scope="col"
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
              >
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="bg-white divide-y divide-gray-200">
          {data.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {headerColumns.map((col) => (
                <td
                  key={`${rowIndex}-${col}`}
                  className="px-6 py-4 whitespace-nowrap text-sm text-gray-700"
                >
                   {/* Basic display, format dates/numbers nicely later */}
                  {typeof row[col] === 'object' ? JSON.stringify(row[col]) : row[col]}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};

export default DataTable;
