 // frontend/src/components/Results/ChartView.js
import React from 'react';
// Example using Recharts (make sure to install it: npm install recharts)
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const ChartView = ({ config, data }) => {
  if (!config || !data || data.length === 0) {
    return null; // Don't render if no config or data
  }

  const { type, x_axis, y_axis } = config;

  if (!x_axis || !y_axis) {
      console.warn("Chart config missing x_axis or y_axis", config);
      return <p className="text-red-500 text-sm">Chart configuration incomplete.</p>;
  }

  // Basic chart rendering based on type
  const renderChart = () => {
    switch (type) {
      case 'line':
        return (
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={x_axis} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Line type="monotone" dataKey={y_axis} stroke="#8884d8" activeDot={{ r: 8 }} />
          </LineChart>
        );
      case 'bar':
        return (
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey={x_axis} />
            <YAxis />
            <Tooltip />
            <Legend />
            <Bar dataKey={y_axis} fill="#82ca9d" />
          </BarChart>
        );
      default:
        console.warn(`Unsupported chart type: ${type}`);
        return <p className="text-orange-500 text-sm">Chart type '{type}' not implemented yet.</p>;
    }
  };

  return (
     <div className="my-4 p-4 bg-white shadow rounded-lg border border-gray-200" style={{ height: '400px' }}> {/* Fixed height container */}
        <h4 className="text-lg font-semibold mb-2 text-gray-700">Visualization ({type} chart)</h4>
        <ResponsiveContainer width="100%" height="90%">
            {renderChart()}
        </ResponsiveContainer>
    </div>
  );
};

export default ChartView;
