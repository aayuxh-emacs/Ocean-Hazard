import React, { useState, useEffect, useCallback } from 'react';
import { AlertTriangle, MapPin, Clock, Shield, Eye, Waves, AlertCircle } from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const OceanHazardDashboard = () => {
  const [hazardData, setHazardData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [selectedLocation, setSelectedLocation] = useState('Santa Monica Beach, California');
  const [userReport, setUserReport] = useState('');
  const [reportLocation, setReportLocation] = useState('');

  const analyzeHazards = useCallback(async (location) => {
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/analyze-hazards', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ location }),
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const hazardInfo = await response.json();
      setHazardData(hazardInfo);
    } catch (error) {
      console.error('Error fetching hazard data:', error);
      setHazardData({
        location,
        analysis_time: new Date().toISOString(),
        overall_risk_level: 'LOW',
        hazards: [],
        safe_areas: [],
        general_conditions: 'Error fetching data',
        last_updated: new Date().toISOString(),
        error: error.message,
      });
    }
    setLoading(false);
  }, []);

  const analyzeUserReport = async () => {
    if (!userReport.trim() || !reportLocation.trim()) return;
    setLoading(true);
    try {
      const response = await fetch('http://localhost:8000/analyze-user-report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ report: userReport, location: reportLocation }),
      });
      if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
      const analysis = await response.json();
      alert(`Report Analysis:\nHazard: ${analysis.is_hazard ? 'Yes' : 'No'}\nUrgency: ${analysis.urgency}\nAction: ${analysis.recommended_action}`);
      setUserReport('');
      setReportLocation('');
    } catch (error) {
      console.error('Error analyzing report:', error);
      alert('Error analyzing report. Please try again.');
    }
    setLoading(false);
  };

  useEffect(() => {
    analyzeHazards(selectedLocation);
  }, [selectedLocation, analyzeHazards]);

  const getRiskColor = (level) => {
    switch (level) {
      case 'LOW': return 'text-green-600 bg-green-100';
      case 'MEDIUM': return 'text-yellow-600 bg-yellow-100';
      case 'HIGH': return 'text-red-600 bg-red-100';
      case 'EXTREME': return 'text-red-800 bg-red-200';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'LOW': return <Shield className="w-4 h-4 text-green-500" />;
      case 'MEDIUM': return <Eye className="w-4 h-4 text-yellow-500" />;
      case 'HIGH': return <AlertTriangle className="w-4 h-4 text-red-500" />;
      case 'EXTREME': return <AlertCircle className="w-4 h-4 text-red-700" />;
      default: return <Shield className="w-4 h-4 text-gray-500" />;
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6 bg-gray-50 min-h-screen">
      <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-4 flex items-center">
          <Waves className="w-8 h-8 text-blue-500 mr-3" />
          Ocean Hazard Monitor
        </h1>
        
        <div className="flex flex-col md:flex-row gap-4 mb-6">
          <div className="flex-1">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Location
            </label>
            <select 
              value={selectedLocation} 
              onChange={(e) => setSelectedLocation(e.target.value)}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            >
              <option>Santa Monica Beach, California</option>
              <option>Venice Beach, California</option>
              <option>Huntington Beach, California</option>
              <option>Malibu Beach, California</option>
              <option>Manhattan Beach, California</option>
            </select>
          </div>
          
          <button 
            onClick={() => analyzeHazards(selectedLocation)}
            disabled={loading}
            className="bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 disabled:opacity-50 flex items-center"
          >
            {loading ? 'Analyzing...' : 'Refresh Analysis'}
          </button>
        </div>
      </div>

      {hazardData && (
        <div className="grid md:grid-cols-2 gap-6 mb-6">
          {/* Overall Risk Status */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h2 className="text-xl font-semibold mb-4 flex items-center">
              <MapPin className="w-5 h-5 mr-2" />
              {hazardData.location}
            </h2>
            
            <div className={`inline-flex items-center px-4 py-2 rounded-full text-sm font-medium mb-4 ${getRiskColor(hazardData.overall_risk_level)}`}>
              Risk Level: {hazardData.overall_risk_level}
            </div>
            
            <div className="space-y-2">
              <div className="flex items-center text-sm text-gray-600">
                <Clock className="w-4 h-4 mr-2" />
                Last Updated: {new Date(hazardData.last_updated).toLocaleTimeString()}
              </div>
              
              <div className="text-sm text-gray-700">
                <strong>Conditions:</strong> {hazardData.general_conditions}
              </div>
            </div>
          </div>

          {/* Safe Areas */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold mb-3 text-green-700">
              Safe Areas
            </h3>
            <div className="space-y-2">
              {hazardData.safe_areas?.map((area, index) => (
                <div key={index} className="flex items-center text-sm text-green-600">
                  <Shield className="w-4 h-4 mr-2" />
                  {area}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Map for Hazard Locations */}
      {hazardData?.hazards?.some(hazard => hazard.coordinates) && (
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h3 className="text-xl font-semibold mb-4">Hazard Map</h3>
          <MapContainer center={[34.0195, -118.4912]} zoom={13} style={{ height: '400px', width: '100%' }}>
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            {hazardData.hazards
              .filter(hazard => hazard.coordinates)
              .map((hazard, index) => {
                const [lat, lng] = hazard.coordinates.split(',').map(Number);
                return (
                  <Marker key={index} position={[lat, lng]}>
                    <Popup>
                      <strong>{hazard.type.replace('_', ' ')}</strong><br />
                      {hazard.description}<br />
                      Severity: {hazard.severity}<br />
                      Source: {hazard.source}
                    </Popup>
                  </Marker>
                );
              })}
          </MapContainer>
        </div>
      )}

      {/* Active Hazards */}
      {hazardData?.hazards?.length > 0 && (
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <h3 className="text-xl font-semibold mb-4 text-red-700">Active Hazards</h3>
          <div className="grid gap-4">
            {hazardData.hazards.map((hazard, index) => (
              <div key={index} className="border-l-4 border-red-500 pl-4 py-3 bg-red-50 rounded-r-lg">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center">
                    {getSeverityIcon(hazard.severity)}
                    <span className="ml-2 font-medium text-gray-800 capitalize">
                      {hazard.type.replace('_', ' ')}
                    </span>
                  </div>
                  <span className={`px-2 py-1 rounded text-xs font-medium ${getRiskColor(hazard.severity)}`}>
                    {hazard.severity}
                  </span>
                </div>
                
                <p className="text-gray-700 mb-2">{hazard.description}</p>
                
                <div className="grid md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <strong>Location:</strong> {hazard.location_specific}
                  </div>
                  <div>
                    <strong>Reported:</strong> {hazard.reported_time}
                  </div>
                  <div>
                    <strong>Source:</strong> {hazard.source}
                  </div>
                  <div>
                    <strong>Credibility:</strong> 
                    <span className={`ml-1 ${hazard.credibility === 'HIGH' ? 'text-green-600' : hazard.credibility === 'MEDIUM' ? 'text-yellow-600' : 'text-red-600'}`}>
                      {hazard.credibility}
                    </span>
                  </div>
                </div>
                
                <div className="mt-3 p-2 bg-blue-50 rounded text-sm">
                  <strong>Recommended Action:</strong> {hazard.recommended_action}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* User Report Section */}
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-xl font-semibold mb-4">Report Ocean Conditions</h3>
        <div className="grid md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Location
            </label>
            <input
              type="text"
              value={reportLocation}
              onChange={(e) => setReportLocation(e.target.value)}
              placeholder="e.g., Venice Beach, California"
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>
        
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Describe the conditions or hazard you observed
          </label>
          <textarea
            value={userReport}
            onChange={(e) => setUserReport(e.target.value)}
            placeholder="e.g., Saw jellyfish near the pier, large waves making swimming dangerous, debris in the water..."
            rows="3"
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
          />
        </div>
        
        <button
          onClick={analyzeUserReport}
          disabled={loading || !userReport.trim() || !reportLocation.trim()}
          className="bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 disabled:opacity-50"
        >
          {loading ? 'Analyzing Report...' : 'Submit Report'}
        </button>
      </div>
    </div>
  );
};

export default OceanHazardDashboard;