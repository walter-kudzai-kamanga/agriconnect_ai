import React, { useState, useEffect } from 'react';
import { Users, Truck, MapPin, Calendar, Star } from 'lucide-react';

const Users = () => {
  const [users, setUsers] = useState({ farmers: [], transporters: [] });
  const [activeTab, setActiveTab] = useState('farmers');

  useEffect(() => {
    // Mock data fetch
    setTimeout(() => {
      setUsers({
        farmers: [
          { id: 1, name: 'John Moyo', location: 'Mashonaland East', joinDate: '2024-01-15', completedJobs: 12, phone: '+263771234567' },
          { id: 2, name: 'Sarah Ndlovu', location: 'Mashonaland Central', joinDate: '2024-02-20', completedJobs: 8, phone: '+263772345678' },
          { id: 3, name: 'David Chiweshe', location: 'Masvingo', joinDate: '2024-03-10', completedJobs: 5, phone: '+263773456789' },
          { id: 4, name: 'Grace Makoni', location: 'Manicaland', joinDate: '2024-04-05', completedJobs: 15, phone: '+263774567890' },
        ],
        transporters: [
          { id: 1, name: 'Tinashe Transport', vehicleType: 'truck', capacity: 2000, rating: 4.5, completedJobs: 45, phone: '+263775678901' },
          { id: 2, name: 'Blessing Deliveries', vehicleType: 'van', capacity: 800, rating: 4.2, completedJobs: 32, phone: '+263776789012' },
          { id: 3, name: 'Chido Couriers', vehicleType: 'pickup', capacity: 500, rating: 4.7, completedJobs: 28, phone: '+263777890123' },
        ]
      });
    }, 1000);
  }, []);

  const UserCard = ({ user, type }) => (
    <div style={{ 
      background: 'white', 
      padding: '20px', 
      borderRadius: '12px', 
      boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
      marginBottom: '15px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '15px', marginBottom: '15px' }}>
        <div style={{ 
          width: '50px', 
          height: '50px', 
          borderRadius: '50%', 
          background: type === 'farmer' ? '#f0fdf4' : '#eff6ff',
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'center',
          color: type === 'farmer' ? '#16a34a' : '#3b82f6'
        }}>
          {type === 'farmer' ? <Users size={24} /> : <Truck size={24} />}
        </div>
        <div style={{ flex: 1 }}>
          <h3 style={{ margin: '0 0 5px 0', color: '#1e293b' }}>{user.name}</h3>
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#64748b', fontSize: '0.9rem' }}>
              <MapPin size={14} />
              {user.location}
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#64748b', fontSize: '0.9rem' }}>
              <Calendar size={14} />
              Joined {user.joinDate}
            </div>
            {type === 'transporter' && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '5px', color: '#64748b', fontSize: '0.9rem' }}>
                <Star size={14} fill="#f59e0b" color="#f59e0b" />
                {user.rating}
              </div>
            )}
          </div>
        </div>
      </div>
      
      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: type === 'farmer' ? '1fr 1fr' : '1fr 1fr 1fr',
        gap: '15px',
        padding: '15px',
        background: '#f8fafc',
        borderRadius: '8px'
      }}>
        <div>
          <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '5px' }}>Completed Jobs</div>
          <div style={{ fontSize: '1.2rem', fontWeight: 'bold', color: '#1e293b' }}>{user.completedJobs}</div>
        </div>
        {type === 'transporter' && (
          <div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '5px' }}>Vehicle Type</div>
            <div style={{ fontSize: '1rem', fontWeight: 'bold', color: '#1e293b', textTransform: 'capitalize' }}>
              {user.vehicleType}
            </div>
          </div>
        )}
        {type === 'transporter' && (
          <div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '5px' }}>Capacity</div>
            <div style={{ fontSize: '1rem', fontWeight: 'bold', color: '#1e293b' }}>
              {user.capacity} kg
            </div>
          </div>
        )}
        {type === 'farmer' && (
          <div>
            <div style={{ fontSize: '0.8rem', color: '#64748b', marginBottom: '5px' }}>Contact</div>
            <div style={{ fontSize: '1rem', color: '#1e293b' }}>{user.phone}</div>
          </div>
        )}
      </div>
    </div>
  );

  return (
    <div className="dashboard">
      <h1 style={{ marginBottom: '20px', color: '#1e293b' }}>User Management</h1>

      <div style={{ marginBottom: '20px' }}>
        <div style={{ 
          display: 'flex', 
          gap: '10px', 
          borderBottom: '2px solid #e2e8f0',
          paddingBottom: '10px'
        }}>
          <button
            onClick={() => setActiveTab('farmers')}
            style={{
              padding: '10px 20px',
              background: activeTab === 'farmers' ? '#16a34a' : 'transparent',
              color: activeTab === 'farmers' ? 'white' : '#64748b',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: '600'
            }}
          >
            Farmers ({users.farmers.length})
          </button>
          <button
            onClick={() => setActiveTab('transporters')}
            style={{
              padding: '10px 20px',
              background: activeTab === 'transporters' ? '#16a34a' : 'transparent',
              color: activeTab === 'transporters' ? 'white' : '#64748b',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer',
              fontWeight: '600'
            }}
          >
            Transporters ({users.transporters.length})
          </button>
        </div>
      </div>

      <div>
        {activeTab === 'farmers' && (
          <div>
            <h2 style={{ marginBottom: '20px', color: '#1e293b' }}>Registered Farmers</h2>
            {users.farmers.map(farmer => (
              <UserCard key={farmer.id} user={farmer} type="farmer" />
            ))}
          </div>
        )}

        {activeTab === 'transporters' && (
          <div>
            <h2 style={{ marginBottom: '20px', color: '#1e293b' }}>Transport Partners</h2>
            {users.transporters.map(transporter => (
              <UserCard key={transporter.id} user={transporter} type="transporter" />
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Users;