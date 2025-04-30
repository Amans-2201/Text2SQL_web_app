import React from 'react';
import { 
    LineChart, Line, BarChart, Bar, PieChart, Pie, ScatterChart, Scatter,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell
} from 'recharts';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

const ChartView = ({ config, data }) => {
    if (!config) return null;

    const { 
        type = 'bar', 
        title = 'Data Visualization', 
        x_axis, 
        y_axis, 
        processedData = null,
        description = '' 
    } = config;

    // Use processed data if available, otherwise use raw data
    const chartData = processedData || data;
    
    if (!chartData || chartData.length === 0) return null;

    const renderChart = () => {
        // Add console logs for debugging
        console.log('Chart type:', type);
        console.log('Chart data:', chartData);
        console.log('X-axis:', x_axis);
        console.log('Y-axis:', y_axis);

        switch (type.toLowerCase()) {
            case 'line':
                return (
                    <LineChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey={x_axis} />
                        <YAxis dataKey={y_axis} />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey={y_axis} stroke="#8884d8" />
                    </LineChart>
                );

            case 'bar':
                return (
                    <BarChart data={chartData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey={x_axis} />
                        <YAxis dataKey={y_axis} />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey={y_axis} fill="#8884d8" />
                    </BarChart>
                );

            case 'pie':
                return (
                    <PieChart>
                        <Pie
                            data={chartData}
                            dataKey={y_axis}
                            nameKey={x_axis}
                            cx="50%"
                            cy="50%"
                            outerRadius={80}
                            label
                        >
                            {chartData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                    </PieChart>
                );

            default:
                return null;
        }
    };

    return (
        <div className="my-4 p-4 bg-white dark:bg-gray-800 shadow rounded-lg border border-gray-200 dark:border-gray-700">
            <h3 className="text-lg font-semibold mb-2 text-gray-700 dark:text-gray-200">{title}</h3>
            {description && (
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{description}</p>
            )}
            <div style={{ width: '100%', height: 400 }}>
                <ResponsiveContainer>
                    {renderChart()}
                </ResponsiveContainer>
            </div>
        </div>
    );
};

export default ChartView;
