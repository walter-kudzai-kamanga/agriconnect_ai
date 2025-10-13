import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  Users, 
  Truck, 
  Package,
  Shield,
  Activity
} from 'lucide-react';
import { 
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';

const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [performanceData, setPerformanceData] = useState([]);
  const [recentJobs, setRecentJobs] = useState([]);

  useEffect(() => {
    // Mock data fetch - replace with actual API calls
    const fetchDashboardData = async () => {
      // Simulate API call
      setTimeout(() => {
        setStats({
          totalJobs: 156,
          completedJobs: 128,
          inProgressJobs: 15,
          pendingJobs: 13,
          totalFarmers: 89,
          totalTransporters: 34,
          totalProduceKg: 45200,
          spoilagePreventedKg: 1250,
          successRate: 82.1
        });

        setPerformanceData([
          { date: 'Jan', jobs: 45, produce: 12500 },
          { date: 'Feb', jobs: 52, produce: 14200 },
          { date: 'Mar', jobs: 48, produce: 13200 },
          { date: 'Apr', jobs: 61, produce: 16800 },
          { date: 'May', jobs: 65, produce: 18200 },
          { date: 'Jun', jobs: 72, produce: 20100 },
        ]);

        setRecentJobs([
          { id: 1, farmer: 'John Moyo', crop: 'Tomatoes', quantity: 500, status: 'completed', date: '2024-06-15' },
          { id: 2, farmer: 'Sarah Ndlovu', crop: 'Maize', quantity: 1000, status: 'in-progress', date: '2024-06-15' },
          { id: 3, farmer: 'David Chiweshe', crop: 'Beans', quantity: 300, status: 'pending', date: '2024-06-14' },
          { id: 4, farmer: 'Grace Makoni', crop: 'Potatoes', quantity: 750, status: 'completed', date: '2024-06-14' },
        ]);
      }, 1000);
    };

    fetchDashboardData();
  }, []);

  if (!stats) {
    return <div className="dashboard">Loading...</div>;
  }

  const cropData = [
    { name: 'Tomatoes', value: 35 },
    { name: 'Maize', value: 25 },
    { name: 'Beans', value: 15 },
    { name: 'Potatoes', value: 15 },
    { name: 'Other', value: 10 },
  ];

  const COLORS = ['#16a34a', '#f59e0b', '#ef4444', '#3b82f6', '#8b5cf6'];

  const StatCard = ({ title, value, trend, icon: Icon }) => (
    <div className="stat-card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h3>{title}</h3>
          <div className="value">{value}</div>
          {trend && (
            <div className={`trend ${trend.direction}`}>
              {trend.direction === 'positive' ? <TrendingUp size={16} /> : <TrendingDown size={16} />}
              {trend.value}
            </div>
          )}
        </div>
        <div style={{ 
          padding: '12px', 
          backgroundColor: '#f0fdf4', 
          borderRadius: '8px',
          color: '#16a34a'
        }}>
          <Icon size={24} />
        </div>
      </div>
    </div>
  );

  return (
    <div className="dashboard">
      <h1 style={{ marginBottom: '20px', color: '#1e293b' }}>Dashboard Overview</h1>
      
      <div className="stats-grid">
        <StatCard 
          title="Total Jobs" 
          value={stats.totalJobs} 
          trend={{ direction: 'positive', value: '+12%' }}
          icon={Activity}
        />
        <StatCard 
          title="Completed Jobs" 
          value={stats.completedJobs} 
          trend={{ direction: 'positive', value: '+8%' }}
          icon={Package}
        />
        <StatCard 
          title="Active Farmers" 
          value={stats.totalFarmers} 
          trend={{ direction: 'positive', value: '+15%' }}
          icon={Users}
        />
        <StatCard 
          title="Transport Partners" 
          value={stats.totalTransporters} 
          trend={{ direction: 'positive', value: '+5%' }}
          icon={Truck}
        />
      </div>

      <div className="charts-grid">
        <div className="chart-card">
          <h3>Platform Performance</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="jobs" stroke="#16a34a" name="Jobs Completed" />
              <Line type="monotone" dataKey="produce" stroke="#3b82f6" name="Produce (kg)" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-card">
          <h3>Crop Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={cropData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {cropData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '20px' }}>
        <div className="chart-card">
          <h3>Recent Transport Activity</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={performanceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="jobs" fill="#16a34a" name="Jobs" />
              <Bar dataKey="produce" fill="#f59e0b" name="Produce (tons)" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="recent-activity">
          <h3 style={{ marginBottom: '20px' }}>Recent Jobs</h3>
          {recentJobs.map((job) => (
            <div key={job.id} className="activity-item">
              <div className="activity-icon">
                <Package size={16} />
              </div>
              <div className="activity-content">
                <h4>{job.farmer}</h4>
                <p>{job.quantity}kg of {job.crop}</p>
                <div className="activity-time">{job.date}</div>
              </div>
              <span className={`status-badge status-${job.status}`}>
                {job.status}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;