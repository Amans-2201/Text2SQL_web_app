import React, { useEffect, useState, memo, useCallback } from 'react';
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

  // Memoize fetch functions
  const fetchDbInfo = useCallback(async () => {
    try {
      const response = await apiClient.get('/chat/database-info');
      if (response.data) {
        setDbInfo(prev => ({
          ...prev,
          dbName: response.data.dbName,
          tables: response.data.tables || []
        }));
      }
    } catch (error) {
      console.error('Failed to fetch database info:', error);
    } finally {
      setInitialLoading(false);
    }
  }, []);

  const handleTableClick = useCallback(async (tableName) => {
    try {
      if (selectedTable === tableName) {
        setSelectedTable(null);
        return;
      }

      setSelectedTable(tableName);
      setLoading(prev => ({ ...prev, [tableName]: true }));

      if (!dbInfo.columns[tableName]) {
        const response = await apiClient.get(`/chat/table-columns/${tableName}`);
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

  useEffect(() => {
    fetchDbInfo();
  }, [fetchDbInfo]);

  if (initialLoading) {
    return (
      <div className="bg-gray-800 dark:bg-gray-900 text-white w-64 min-w-[16rem] p-4 flex items-center justify-center">
        <div className="animate-spin h-6 w-6 border-2 border-blue-500 rounded-full border-t-transparent"></div>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 dark:bg-gray-900 text-white w-64 min-w-[16rem] p-4 flex flex-col h-full">
      <div className="mb-6">
        <h2 className="text-lg font-semibold mb-2">Database</h2>
        <p className="text-gray-300">{dbInfo.dbName}</p>
      </div>
      
      <div className="flex-grow overflow-y-auto">
        <h3 className="text-md font-semibold mb-3">Tables</h3>
        <div className="space-y-2">
          {dbInfo.tables.map((table) => (
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
                  {dbInfo.columns[table].map((column, idx) => (
                    <div key={idx} className="pl-2 text-gray-300 py-1">
                      {column}
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default memo(DatabaseInfo);