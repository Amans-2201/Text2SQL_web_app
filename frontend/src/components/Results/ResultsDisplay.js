 // frontend/src/components/Results/ResultsDisplay.js
import React from 'react';
import DataTable from './DataTable';
import ChartView from './ChartView';
import SummaryText from './SummaryText';
import LoadingSpinner from '../Common/LoadingSpinner';

const ResultsDisplay = ({ result, isLoading }) => {
    if (isLoading) {
        return (
            <div className="flex justify-center items-center p-10">
                <LoadingSpinner size="w-12 h-12" />
                <span className="ml-4 text-gray-600">Fetching results...</span>
            </div>
        );
    }

    // Handle initial state or no result yet
    if (!result) {
         return <div className="p-4 text-center text-gray-500 italic">Ask a question to see results here.</div>;
    }

    // Handle errors returned from the backend
    if (result.error) {
        return (
            <div className="m-4 p-4 bg-red-100 border border-red-300 text-red-800 rounded-lg shadow">
                <h4 className="font-bold mb-2">Error</h4>
                <p style={{ whiteSpace: 'pre-wrap' }}>{result.error}</p>
                 {result.query && (
                     <div className='mt-2'>
                        <p className='text-xs text-red-700'>Attempted Query:</p>
                        <pre className='text-xs bg-red-50 p-1 rounded overflow-x-auto'>{result.query}</pre>
                    </div>
                 )}
            </div>
        );
    }

    // Destructure successful result
    const { query, data, columns, summary, visualization } = result;
    const showChart = visualization && visualization.type !== 'table' && data && data.length > 0;
    const showTable = data && data.length > 0;

    return (
        <div className="p-4 space-y-4">
             {/* Optionally display the executed SQL query */}
             {query && (
                <details className="bg-gray-50 p-2 rounded border border-gray-200 text-xs text-gray-600">
                     <summary className="cursor-pointer font-medium">Show SQL Query</summary>
                     <pre className="mt-1 bg-white p-2 rounded overflow-x-auto">{query}</pre>
                </details>
             )}

            {/* Display Summary */}
            <SummaryText summary={summary} />

            {/* Display Chart if suggested and applicable */}
            {showChart && <ChartView config={visualization} data={data} />}

            {/* Display Table */}
            {showTable && <DataTable columns={columns} data={data} />}

             {/* Message if query ran but returned no data */}
             {data && data.length === 0 && !summary?.includes("No data found") && (
                 <p className="text-center text-gray-500 italic my-4">The query ran successfully but returned no data.</p>
             )}
        </div>
    );
};

export default ResultsDisplay;
