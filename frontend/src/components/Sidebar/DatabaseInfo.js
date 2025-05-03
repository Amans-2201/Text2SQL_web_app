import React, { useEffect, useState, useCallback } from 'react';
import apiClient from '../../services/api';

const DatabaseInfo = () => {
  const [dbInfo, setDbInfo] = useState({
    dbName: '',
    tables: [],
    columns: {}
  });
  const [selectedTable, setSelectedTable] = useState(null);
  const [loading, setLoading] = useState({});
  const [initialLoading, setInitialLoading] = useState(true);
  const [error, setError] = useState(null);

  // Force refresh when needed
  const forceRefresh = useCallback(async () => {
    setInitialLoading(true);
    setError(null);
    
    try {
      // Add timestamp parameter to prevent caching
      const timestamp = Date.now();
      const response = await apiClient.get(`/chat/database-info?t=${timestamp}`);
      
      console.log("Fresh database info:", response.data);
      
      if (response.data) {
        setDbInfo(prev => ({
          ...prev,
          dbName: response.data.dbName || '',
          tables: response.data.tables || [],
          columns: {} // Clear column cache
        }));
      }
    } catch (error) {
      console.error('Failed to fetch database info:', error);
      setError('Failed to load database information');
    } finally {
      setInitialLoading(false);
    }
  }, []);

  // Run on component mount
  useEffect(() => {
    forceRefresh();
    
    // Also run when config has been updated
    const checkConfigChange = () => {
      const lastUpdate = localStorage.getItem('configUpdated');
      if (lastUpdate && !window.lastProcessedUpdate) {
        window.lastProcessedUpdate = lastUpdate;
        forceRefresh();
      }
    };
    
    // Check every few seconds
    const intervalId = setInterval(checkConfigChange, 2000);
    return () => clearInterval(intervalId);
  }, [forceRefresh]);

  const handleTableClick = useCallback(async (tableName) => {
    try {
      if (selectedTable === tableName) {
        setSelectedTable(null);
        return;
      }

      setSelectedTable(tableName);
      setLoading(prev => ({ ...prev, [tableName]: true }));

      if (!dbInfo.columns[tableName]) {
        // Add timestamp to prevent caching
        const timestamp = new Date().getTime();
        const response = await apiClient.get(`/chat/table-columns/${tableName}?t=${timestamp}`);
        
        console.log(`TABLE COLUMNS RESPONSE for ${tableName}:`, response.data);
        
        if (response.data?.columns) {
          setDbInfo(prev => ({
            ...prev,
            columns: {
              ...prev.columns,
              [tableName]: response.data.columns
            }
          }));
        }
      }
    } catch (error) {
      console.error(`Failed to fetch columns for ${tableName}:`, error);
    } finally {
      setLoading(prev => ({ ...prev, [tableName]: false }));
    }
  }, [selectedTable, dbInfo.columns]);

  if (initialLoading) {
    return (
      <div className="bg-gray-800 text-white w-64 min-w-[16rem] p-4 flex items-center justify-center">
        <div className="animate-spin h-6 w-6 border-2 border-blue-500 rounded-full border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 text-white w-64 min-w-[16rem] p-4 flex flex-col h-full">
      <div className="mb-6">
        <h2 className="text-lg font-semibold mb-2">Database</h2>
        <div className="flex justify-between items-center">
          <p className="text-gray-300">{dbInfo.dbName}</p>
          <button 
            onClick={forceRefresh} 
            className="text-xs text-blue-400 hover:text-blue-300"
            title="Refresh database information"
          >
            Refresh
          </button>
        </div>
        {error && <p className="text-red-400 text-sm mt-2">{error}</p>}
      </div>
      
      <div className="flex-grow overflow-y-auto">
        <h3 className="text-md font-semibold mb-3">Tables</h3>
        <div className="space-y-2">
          {dbInfo.tables.length === 0 ? (
            <p className="text-gray-400 italic">No tables found</p>
          ) : (
            dbInfo.tables.map((table) => (
              <div key={table} className="space-y-2">
                <div
                  className={`p-2 rounded cursor-pointer transition-colors duration-200 ${
                    selectedTable === table 
                      ? 'bg-blue-600 hover:bg-blue-700' 
                      : 'bg-gray-700 hover:bg-gray-600'
                  }`}
                  onClick={() => handleTableClick(table)}
                >
                  <div className="flex items-center justify-between">
                    <span>{table}</span>
                    {loading[table] && (
                      <div className="animate-spin h-4 w-4 border-2 border-blue-500 rounded-full border-t-transparent"></div>
                    )}
                  </div>
                </div>
                {selectedTable === table && dbInfo.columns[table] && (
                  <div className="ml-4 p-2 bg-gray-700 rounded text-sm">
                    <div className="font-medium mb-1 text-blue-300">Columns:</div>
                    {dbInfo.columns[table].length > 0 ? (
                      dbInfo.columns[table].map((column, idx) => (
                        <div key={idx} className="pl-2 text-gray-300 py-1">
                          {column}
                        </div>
                      ))
                    ) : (
                      <div className="pl-2 text-gray-400 italic">No columns found</div>
                    )}
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

export default React.memo(DatabaseInfo);