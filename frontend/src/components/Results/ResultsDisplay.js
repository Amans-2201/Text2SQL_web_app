// frontend/src/components/Results/ResultsDisplay.js
import React, { useState } from 'react';
import DataTable from './DataTable';
import ChartView from './ChartView';
import SummaryText from './SummaryText';
import LoadingSpinner from '../Common/LoadingSpinner';

const ResultsDisplay = ({ result, isLoading }) => {
    const [copySuccess, setCopySuccess] = useState('');

    // Add copy to clipboard function
    const copyToClipboard = async (text) => {
        try {
            await navigator.clipboard.writeText(text);
            setCopySuccess('Copied!');
            setTimeout(() => setCopySuccess(''), 2000); // Clear message after 2 seconds
        } catch (err) {
            setCopySuccess('Failed to copy');
            console.error('Failed to copy text: ', err);
        }
    };

    // SQL query formatter function
    const formatSqlQuery = (sql) => {
        if (!sql) return '';
        
        // Define SQL keywords for proper formatting
        const keywords = [
            'SELECT', 'FROM', 'WHERE', 'JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 
            'OUTER JOIN', 'ON', 'AND', 'OR', 'GROUP BY', 'ORDER BY', 'HAVING', 
            'LIMIT', 'OFFSET', 'UNION', 'ALL', 'AS', 'DISTINCT', 'COUNT', 'SUM', 
            'AVG', 'MIN', 'MAX', 'CASE', 'WHEN', 'THEN', 'ELSE', 'END', 'IN'
        ];
        
        // Replace keywords with line breaks and proper indentation
        let formattedSql = sql.trim();
        
        // Add line breaks for main clauses
        keywords.forEach(keyword => {
            // Skip column aliases with AS
            if (keyword === 'AS') return;
            
            const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
            formattedSql = formattedSql.replace(regex, (match) => {
                // Different indentation based on keyword
                if (['SELECT', 'FROM', 'WHERE', 'GROUP BY', 'ORDER BY', 'HAVING'].includes(match.toUpperCase())) {
                    return `\n${match.toUpperCase()}`;
                } else if (['JOIN', 'LEFT JOIN', 'RIGHT JOIN', 'INNER JOIN', 'OUTER JOIN'].includes(match.toUpperCase())) {
                    return `\n${match.toUpperCase()}`;
                } else if (['ON', 'AND', 'OR'].includes(match.toUpperCase())) {
                    return `\n    ${match.toUpperCase()}`;
                }
                return match.toUpperCase();
            });
        });
        
        // Format commas in SELECT clause
        formattedSql = formattedSql.replace(/,\s*/g, ',\n    ');
        
        // Apply color to keywords
        keywords.forEach(keyword => {
            const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
            formattedSql = formattedSql.replace(regex, match => 
                `<span class="text-purple-600 font-medium">${match.toUpperCase()}</span>`
            );
        });
        
        // Add proper indentation after SELECT
        formattedSql = formattedSql.replace(/SELECT\b/i, 'SELECT\n    ');
        
        return formattedSql;
    };

    // Add CSV export function
    const exportToCSV = (data, columns) => {
        if (!data || !columns) return;

        const headers = columns.join(',');
        const csvRows = data.map(row => 
            columns.map(col => {
                let cell = row[col];
                // Handle cells that contain commas or quotes
                if (typeof cell === 'string' && (cell.includes(',') || cell.includes('"'))) {
                    cell = `"${cell.replace(/"/g, '""')}"`;
                }
                return cell;
            }).join(',')
        );

        const csvContent = [headers, ...csvRows].join('\n');
        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        const url = URL.createObjectURL(blob);
        
        link.setAttribute('href', url);
        link.setAttribute('download', `query_results_${new Date().toISOString()}.csv`);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

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
            {/* Export CSV button section */}
            {result?.data && result?.data.length > 0 && (
                <div className="flex justify-end gap-2">
                    <button
                        onClick={() => exportToCSV(result.data, result.columns)}
                        className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 flex items-center gap-2"
                    >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                        </svg>
                        Export to CSV
                    </button>
                </div>
            )}

            {/* SQL Query section with formatted query */}
            {result?.query && (
                <details className="bg-gray-50 p-2 rounded border border-gray-200 text-xs text-gray-600">
                    <summary className="cursor-pointer font-medium flex items-center justify-between">
                        <span>Show SQL Query</span>
                        <div className="flex items-center gap-2">
                            {copySuccess && (
                                <span className="text-green-600 text-xs">{copySuccess}</span>
                            )}
                            <button
                                onClick={(e) => {
                                    e.preventDefault(); // Prevent details from toggling
                                    copyToClipboard(result.query);
                                }}
                                className="px-2 py-1 text-xs bg-blue-100 text-blue-700 rounded hover:bg-blue-200 flex items-center gap-1"
                            >
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                                </svg>
                                Copy Query
                            </button>
                        </div>
                    </summary>
                    <div className="mt-2 bg-white p-3 rounded text-sm sql-container">
                        <pre 
                            className="font-mono text-gray-800" 
                            dangerouslySetInnerHTML={{ __html: formatSqlQuery(result.query) }}
                        />
                    </div>
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
