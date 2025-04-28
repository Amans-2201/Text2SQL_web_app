// frontend/src/components/Results/SummaryText.js
import React from 'react';

const SummaryText = ({ summary }) => {
  if (!summary) return null;

  return (
    <div className="my-4 p-4 bg-blue-50 border border-blue-200 rounded-lg shadow">
      <h4 className="text-md font-semibold mb-2 text-blue-800">Summary</h4>
      <p className="text-gray-700">{summary}</p>
    </div>
  );
};

export default SummaryText; 
