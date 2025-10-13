import React, { useState, useEffect } from 'react';
import { Search, Filter, Download, Eye } from 'lucide-react';

const Jobs = () => {
  const [jobs, setJobs] = useState([]);
  const [filter, setFilter] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    // Mock data fetch
    setTimeout(() => {
      setJobs([
        { 
          id: 1, 
          farmer: 'John Moyo', 
          crop: 'Tomatoes', 
          quantity: 500, 
          pickup: 'Mashonaland East', 
          destination: 'Mbare Musika',
          transporter: 'Tinashe Transport',
          status: 'completed',
          date: '2024-06-15',
          spoilageRisk: 0.15,
          distance: 45
        },
        { 
          id: 2, 
          farmer: 'Sarah Ndlovu', 
          crop: 'Maize', 
          quantity: 1000, 
          pickup: 'Mashonaland Central', 
          destination: 'Sakubva Market',
          transporter: 'Blessing Deliveries',
          status: 'in-progress',
          date: '2024-06-15',
          spoilageRisk: 0.08,
          distance: 85
        },
        { 
          id: 3, 
          farmer: 'David Chiweshe', 
          crop: 'Beans', 
          quantity: 300, 
          pickup: 'Masvingo', 
          destination: 'Mbare Musika',
          transporter: null,
          status: 'pending',
          date: '2024-06-14',
          spoilageRisk: 0.12,
          distance: 290
        },
        { 
          id: 4, 
          farmer: 'Grace Makoni', 
          crop: 'Potatoes', 
          quantity: 750, 
          pickup: 'Manicaland', 
          destination: 'Sakubva Market',
          transporter: 'Chido Couriers',
          status: 'completed',
          date: '2024-06-14',
          spoilageRisk: 0.15,
          distance: 120
        },
      ]);
    }, 1000);
  }, []);

  const filteredJobs = jobs.filter(job => {
    const matchesFilter = filter === 'all' || job.status === filter;
    const matchesSearch = job.farmer.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         job.crop.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesFilter && matchesSearch;
  });

  const getStatusBadge = (status) => {
    const statusConfig = {
      'completed': { label: 'Completed', color: '#16a34a', bg: '#f0fdf4' },
      'in-progress': { label: 'In Progress', color: '#d97706', bg: '#fffbeb' },
      'pending': { label: 'Pending', color: '#dc2626', bg: '#fef2f2' }
    };
    
    const config = statusConfig[status];
    return (
      <span style={{
        padding: '4px 12px',
        borderRadius: '20px',
        fontSize: '0.8rem',
        fontWeight: '600',
        textTransform: 'uppercase',
        backgroundColor: config.bg,
        color: config.color
      }}>
        {config.label}
      </span>
    );
  };

  return (
    <div className="dashboard">
      <h1 style={{ marginBottom: '20px', color: '#1e293b' }}>Transport Jobs</h1>

      <div style={{ 
        display: 'flex', 
        gap: '15px', 
        marginBottom: '20px',
        flexWrap: 'wrap'
      }}>
        <div style={{ position: 'relative', flex: '1', minWidth: '300px' }}>
          <Search size={20} style={{ 
            position: 'absolute', 
            left: '12px', 
            top: '50%', 
            transform: 'translateY(-50%)',
            color: '#64748b'
          }} />
          <input
            type="text"
            placeholder="Search jobs by farmer or crop..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{
              width: '100%',
              padding: '12px 12px 12px 40px',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
              fontSize: '1rem'
            }}
          />
        </div>

        <select
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
          style={{
            padding: '12px',
            border: '1px solid #d1d5db',
            borderRadius: '8px',
            fontSize: '1rem',
            minWidth: '150px'
          }}
        >
          <option value="all">All Status</option>
          <option value="pending">Pending</option>
          <option value="in-progress">In Progress</option>
          <option value="completed">Completed</option>
        </select>

        <button style={{
          padding: '12px 20px',
          background: '#16a34a',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          fontWeight: '600'
        }}>
          <Download size={18} />
          Export
        </button>
      </div>

      <div className="table-container">
        <div className="table-header">
          <h3>Recent Transport Jobs</h3>
        </div>
        <table className="table">
          <thead>
            <tr>
              <th>Job ID</th>
              <th>Farmer</th>
              <th>Crop</th>
              <th>Quantity</th>
              <th>Route</th>
              <th>Transporter</th>
              <th>Status</th>
              <th>Date</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {filteredJobs.map((job) => (
              <tr key={job.id}>
                <td style={{ fontWeight: '600', color: '#1e293b' }}>#{job.id}</td>
                <td>{job.farmer}</td>
                <td style={{ textTransform: 'capitalize' }}>{job.crop}</td>
                <td>{job.quantity} kg</td>
                <td>
                  <div style={{ fontSize: '0.9rem' }}>
                    <div style={{ fontWeight: '500' }}>{job.pickup}</div>
                    <div style={{ color: '#64748b', fontSize: '0.8rem' }}>→ {job.destination}</div>
                    <div style={{ color: '#64748b', fontSize: '0.8rem' }}>{job.distance} km</div>
                  </div>
                </td>
                <td>
                  {job.transporter ? (
                    <span style={{ color: '#16a34a', fontWeight: '500' }}>{job.transporter}</span>
                  ) : (
                    <span style={{ color: '#64748b', fontStyle: 'italic' }}>Not assigned</span>
                  )}
                </td>
                <td>{getStatusBadge(job.status)}</td>
                <td style={{ color: '#64748b' }}>{job.date}</td>
                <td>
                  <button style={{
                    padding: '6px 12px',
                    background: 'transparent',
                    border: '1px solid #d1d5db',
                    borderRadius: '6px',
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '5px',
                    fontSize: '0.8rem'
                  }}>
                    <Eye size={14} />
                    View
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', 
        gap: '20px', 
        marginTop: '30px' 
      }}>
        <div className="metric-card">
          <h3>Job Distribution</h3>
          <div style={{ display: 'flex', justifyContent: 'space-around', textAlign: 'center' }}>
            <div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#16a34a' }}>
                {jobs.filter(j => j.status === 'completed').length}
              </div>
              <div style={{ color: '#64748b', fontSize: '0.9rem' }}>Completed</div>
            </div>
            <div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#d97706' }}>
                {jobs.filter(j => j.status === 'in-progress').length}
              </div>
              <div style={{ color: '#64748b', fontSize: '0.9rem' }}>In Progress</div>
            </div>
            <div>
              <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#dc2626' }}>
                {jobs.filter(j => j.status === 'pending').length}
              </div>
              <div style={{ color: '#64748b', fontSize: '0.9rem' }}>Pending</div>
            </div>
          </div>
        </div>

        <div className="metric-card">
          <h3>Total Produce Transported</h3>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#16a34a', marginBottom: '10px' }}>
            {jobs.reduce((total, job) => total + job.quantity, 0).toLocaleString()} kg
          </div>
          <div style={{ color: '#64748b', fontSize: '0.9rem' }}>
            Across {jobs.length} transport jobs
          </div>
        </div>
      </div>
    </div>
  );
};

export default Jobs;