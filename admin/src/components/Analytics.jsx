import React, { useState, useEffect } from 'react';
import { 
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';

const Analytics = () => {
  const [regionalData, setRegionalData] = useState([]);
  const [cropData, setCropData] = useState([]);
  const [performanceData, setPerformanceData] = useState([]);
  const [economicImpact, setEconomicImpact] = useState(null);

  useEffect(() => {
    // Mock data fetch
    setTimeout(() => {
      setRegionalData([
        { region: 'Mashonaland East', jobs: 45, farmers: 23, transporters: 8, produce: 12500 },
        { region: 'Mashonaland Central', jobs: 32, farmers: 18, transporters: 6, produce: 8900 },
        { region: 'Masvingo', jobs: 28, farmers: 15, transporters: 5, produce: 7600 },
        { region: 'Manicaland', jobs: 21, farmers: 12, transporters: 4, produce: 5400 },
      ]);

      setCropData([
        { crop: 'Tomatoes', volume: 8500, jobs: 34, spoilageRisk: 18 },
        { crop: 'Maize', volume: 12000, jobs: 28, spoilageRisk: 8 },
        { crop: 'Beans', volume: 4200, jobs: 15, spoilageRisk: 12 },
        { crop: 'Potatoes', volume: 6800, jobs: 22, spoilageRisk: 15 },
        { crop: 'Cabbage', volume: 3100, jobs: 12, spoilageRisk: 25 },
      ]);

      setPerformanceData([
        { week: 'W1', successRate: 78, avgDeliveryTime: 4.2, spoilageRate: 8.5 },
        { week: 'W2', successRate: 82, avgDeliveryTime: 3.8, spoilageRate: 7.2 },
        { week: 'W3', successRate: 85, avgDeliveryTime: 3.5, spoilageRate: 6.8 },
        { week: 'W4', successRate: 88, avgDeliveryTime: 3.2, spoilageRate: 5.9 },
        { week: 'W5', successRate: 90, avgDeliveryTime: 3.0, spoilageRate: 5.1 },
      ]);

      setEconomicImpact({
        farmerIncome: 52500,
        transporterIncome: 54000,
        spoilageCostSaved: 31250,
        totalImpact: 137750
      });
    }, 1000);
  }, []);

  // Custom tooltip formatter
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div style={{
          backgroundColor: 'white',
          padding: '10px',
          border: '1px solid #ccc',
          borderRadius: '5px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
        }}>
          <p style={{ fontWeight: 'bold', marginBottom: '5px' }}>{label}</p>
          {payload.map((entry, index) => (
            <p key={index} style={{ color: entry.color, margin: '2px 0' }}>
              {entry.name}: {entry.value}
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1200px' }}>
      <h1 style={{ marginBottom: '20px', color: '#1e293b' }}>Analytics & Insights</h1>

      {economicImpact && (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '20px',
          marginBottom: '30px'
        }}>
          <div style={{
            background: 'white',
            padding: '25px',
            borderRadius: '12px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ color: '#1e293b', marginBottom: '15px', fontSize: '1.1rem' }}>
              Farmer Income Generated
            </h3>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#16a34a', marginBottom: '10px' }}>
              ${economicImpact.farmerIncome.toLocaleString()}
            </div>
            <div style={{ color: '#64748b', fontSize: '0.9rem' }}>
              Monthly impact on farmers
            </div>
          </div>
          
          <div style={{
            background: 'white',
            padding: '25px',
            borderRadius: '12px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ color: '#1e293b', marginBottom: '15px', fontSize: '1.1rem' }}>
              Transporter Income
            </h3>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#16a34a', marginBottom: '10px' }}>
              ${economicImpact.transporterIncome.toLocaleString()}
            </div>
            <div style={{ color: '#64748b', fontSize: '0.9rem' }}>
              Monthly earnings for transporters
            </div>
          </div>
          
          <div style={{
            background: 'white',
            padding: '25px',
            borderRadius: '12px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ color: '#1e293b', marginBottom: '15px', fontSize: '1.1rem' }}>
              Spoilage Cost Saved
            </h3>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#16a34a', marginBottom: '10px' }}>
              ${economicImpact.spoilageCostSaved.toLocaleString()}
            </div>
            <div style={{ color: '#64748b', fontSize: '0.9rem' }}>
              Value of prevented food waste
            </div>
          </div>
          
          <div style={{
            background: 'white',
            padding: '25px',
            borderRadius: '12px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
          }}>
            <h3 style={{ color: '#1e293b', marginBottom: '15px', fontSize: '1.1rem' }}>
              Total Economic Impact
            </h3>
            <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#16a34a', marginBottom: '10px' }}>
              ${economicImpact.totalImpact.toLocaleString()}
            </div>
            <div style={{ color: '#64748b', fontSize: '0.9rem' }}>
              Combined monthly impact
            </div>
          </div>
        </div>
      )}

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '20px',
        marginBottom: '30px'
      }}>
        <div style={{
          background: 'white',
          padding: '25px',
          borderRadius: '12px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ color: '#1e293b', marginBottom: '20px', fontSize: '1.2rem' }}>
            Regional Performance
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={regionalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="region" />
              <YAxis />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Bar dataKey="jobs" fill="#16a34a" name="Jobs Completed" />
              <Bar dataKey="produce" fill="#f59e0b" name="Produce (kg)" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div style={{
          background: 'white',
          padding: '25px',
          borderRadius: '12px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ color: '#1e293b', marginBottom: '20px', fontSize: '1.2rem' }}>
            Crop Volume & Risk
          </h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={cropData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="crop" />
              <YAxis yAxisId="left" />
              <YAxis yAxisId="right" orientation="right" />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Bar yAxisId="left" dataKey="volume" fill="#3b82f6" name="Volume (kg)" />
              <Line 
                yAxisId="right"
                type="monotone" 
                dataKey="spoilageRisk" 
                stroke="#ef4444" 
                name="Spoilage Risk %" 
                strokeWidth={2}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{
        background: 'white',
        padding: '25px',
        borderRadius: '12px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
        marginBottom: '20px'
      }}>
        <h3 style={{ color: '#1e293b', marginBottom: '20px', fontSize: '1.2rem' }}>
          Platform Performance Trends
        </h3>
        <ResponsiveContainer width="100%" height={300}>
          <AreaChart data={performanceData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="week" />
            <YAxis />
            <Tooltip content={<CustomTooltip />} />
            <Legend />
            <Area 
              type="monotone" 
              dataKey="successRate" 
              stroke="#16a34a" 
              fill="#16a34a" 
              fillOpacity={0.3}
              name="Success Rate %" 
            />
            <Area 
              type="monotone" 
              dataKey="avgDeliveryTime" 
              stroke="#3b82f6" 
              fill="#3b82f6" 
              fillOpacity={0.3}
              name="Avg Delivery Time (hrs)" 
            />
            <Area 
              type="monotone" 
              dataKey="spoilageRate" 
              stroke="#ef4444" 
              fill="#ef4444" 
              fillOpacity={0.3}
              name="Spoilage Rate %" 
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(2, 1fr)',
        gap: '20px'
      }}>
        <div style={{
          background: 'white',
          padding: '25px',
          borderRadius: '12px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ color: '#1e293b', marginBottom: '20px', fontSize: '1.2rem' }}>
            User Growth
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={[
              { month: 'Jan', farmers: 45, transporters: 12 },
              { month: 'Feb', farmers: 52, transporters: 15 },
              { month: 'Mar', farmers: 61, transporters: 18 },
              { month: 'Apr', farmers: 68, transporters: 22 },
              { month: 'May', farmers: 76, transporters: 27 },
              { month: 'Jun', farmers: 89, transporters: 34 },
            ]}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="month" />
              <YAxis />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Line type="monotone" dataKey="farmers" stroke="#16a34a" name="Farmers" />
              <Line type="monotone" dataKey="transporters" stroke="#3b82f6" name="Transporters" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div style={{
          background: 'white',
          padding: '25px',
          borderRadius: '12px',
          boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ color: '#1e293b', marginBottom: '20px', fontSize: '1.2rem' }}>
            Regional Distribution
          </h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={regionalData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="region" />
              <YAxis />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Bar dataKey="farmers" fill="#16a34a" name="Farmers" />
              <Bar dataKey="transporters" fill="#3b82f6" name="Transporters" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};

export default Analytics;