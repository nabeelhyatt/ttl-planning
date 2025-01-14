import React from 'react';
import { useState, useEffect, useMemo } from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from 'recharts';
import Papa from 'papaparse';

const COLORS = ['#4F46E5', '#7C3AED', '#EC4899', '#F59E0B'];

const MemberAnalysis = () => {
  const [members, setMembers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        const response = await fetch('OBG_Members_Processed.csv');
        const csvText = await response.text();
        Papa.parse(csvText, {
          header: true,
          skipEmptyLines: true,
          complete: (results) => {
            console.log('Parsed data:', results.data);
            setMembers(results.data);
            setLoading(false);
          },
          error: (error) => {
            console.error('Parse error:', error);
            setError(error.message);
            setLoading(false);
          }
        });
      } catch (err) {
        console.error('Fetch error:', err);
        setError(err.message);
        setLoading(false);
      }
    };

    loadData();
  }, []);

  const frequencyData = useMemo(() => {
    if (!members.length) return [];

    const categories = {
      'Very Active (>8x/month)': 0,
      'Active (4-8x/month)': 0,
      'Regular (2-4x/month)': 0,
      'Occasional (1-2x/month)': 0
    };

    members.forEach(member => {
      const visits = parseFloat(member['Visits per month'] || 0);
      if (visits > 8) {
        categories['Very Active (>8x/month)']++;
      } else if (visits >= 4) {
        categories['Active (4-8x/month)']++;
      } else if (visits >= 2) {
        categories['Regular (2-4x/month)']++;
      } else {
        categories['Occasional (1-2x/month)']++;
      }
    });

    return Object.entries(categories).map(([name, value]) => ({
      name,
      value,
      percentage: (value / members.length * 100).toFixed(1)
    }));
  }, [members]);

  const cityData = useMemo(() => {
    if (!members.length) return [];

    const cities = {};
    members.forEach(member => {
      const city = (member.City || '').split('(')[0].trim().split('/')[0];
      if (city) {
        cities[city] = (cities[city] || 0) + 1;
      }
    });

    return Object.entries(cities)
      .sort(([,a], [,b]) => b - a)
      .map(([city, count]) => ({
        city,
        count,
        percentage: (count / members.length * 100).toFixed(1)
      }));
  }, [members]);

  if (loading) return <div className="p-4">Loading member data...</div>;
  if (error) return <div className="p-4 text-red-600">Error loading data: {error}</div>;

  return (
    <div className="space-y-6 p-4 max-w-4xl mx-auto">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-2xl font-bold mb-4">Member Demographics</h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-gray-50 p-4 rounded">
            <h3 className="text-lg font-semibold mb-2">Total Members</h3>
            <p className="text-3xl font-bold">{members.length}</p>
          </div>
          
          <div className="bg-gray-50 p-4 rounded">
            <h3 className="text-lg font-semibold mb-2">Top Cities</h3>
            <div className="space-y-2">
              {cityData.slice(0, 6).map(({city, count, percentage}) => (
                <div key={city} className="flex justify-between">
                  <span>{city}</span>
                  <span className="font-semibold">
                    {count} ({percentage}%)
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div className="mb-8">
          <h3 className="text-lg font-semibold mb-4">Activity Level Distribution</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={frequencyData}
                  dataKey="value"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  label={({name, percentage}) => `${name} (${percentage}%)`}
                >
                  {frequencyData.map((entry, index) => (
                    <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  formatter={(value, name, props) => [
                    `${value} members (${props.payload.percentage}%)`
                  ]}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          
          <div className="mt-4 space-y-2">
            {frequencyData.map((category, index) => (
              <div key={category.name} className="flex justify-between text-sm">
                <div className="flex items-center">
                  <div 
                    className="w-4 h-4 mr-2 rounded" 
                    style={{backgroundColor: COLORS[index % COLORS.length]}}
                  />
                  <span>{category.name}</span>
                </div>
                <span>{category.value} members ({category.percentage}%)</span>
              </div>
            ))}
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50">
                <th className="p-2 text-left">Name</th>
                <th className="p-2 text-left">City</th>
                <th className="p-2 text-left">Favorite Game</th>
                <th className="p-2 text-left">Looking to Play</th>
                <th className="p-2 text-left">Preferred Frequency</th>
              </tr>
            </thead>
            <tbody>
              {members.map((member, index) => (
                <tr key={index} className={index % 2 === 0 ? 'bg-gray-50' : ''}>
                  <td className="p-2">{member.Name}</td>
                  <td className="p-2">{member.City}</td>
                  <td className="p-2">{member['Fav game today']}</td>
                  <td className="p-2">{member['Looking to play']}</td>
                  <td className="p-2">{member['How often you want to play']}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

// Make sure the component is available globally
window.MemberAnalysis = MemberAnalysis;

export default MemberAnalysis;
