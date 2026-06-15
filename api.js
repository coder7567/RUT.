import axios from 'axios';

// Configure the base API URL to point to the FastAPI backend host.
// In a development environment with Android Emulator, 10.0.2.2 points to host localhost.
// For iOS Simulator or physical devices, substitute with the local network server IP.
const API_BASE_URL = 'http://127.0.0.1:8000';

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * UI.2 API Service Layer
 * Calls the FastAPI backend off-road router, bailout, and condition report systems.
 */
export const getRoute = async (startCoord, endCoord, unorthodoxyScore) => {
  const endpoint = '/api/route';
  const fullUrl = `${API_BASE_URL}${endpoint}`;
  const payload = {
    start_coord: startCoord, // [lon, lat]
    end_coord: endCoord,     // [lon, lat]
    unorthodoxy_score: unorthodoxyScore, // float 0.0 - 1.0
  };

  console.log('[TELEMETRY-API] getRoute: Preparing to POST to target URL:', fullUrl);
  console.log('[TELEMETRY-API] getRoute: Raw Payload Object Structure:', JSON.stringify(payload, null, 2));

  try {
    const response = await apiClient.post(endpoint, payload);
    console.log('[TELEMETRY-API] getRoute: Request succeeded! Status:', response.status);
    return response.data;
  } catch (error) {
    console.error('==================== [getRoute TELEMETRY FAILURE DETECTED] ====================');
    console.error('error.message:', error.message);
    console.error('error.code:', error.code);
    if (error.response) {
      console.error('error.response.status (Server Rejected):', error.response.status);
      console.error('error.response.headers:', JSON.stringify(error.response.headers));
      console.error('error.response.data:', JSON.stringify(error.response.data));
    } else {
      console.error('error.response is undefined. The server did not respond or reject with a status code.');
    }
    if (error.request) {
      console.error('error.request is present (Request was sent but no response was received, or blocked by Hermes sandbox)');
      console.error('error.request internal keys:', Object.keys(error.request));
      try {
        console.error('error.request internal metadata stringified:', JSON.stringify(error.request));
      } catch (err) {
        console.error('Failed to stringify error.request:', err.message);
      }
    } else {
      console.error('error.request is undefined. Error occurred before initiating request (client-side configuration/network logic error).');
    }
    console.error('================================================================================');
    throw error;
  }
};

export const triggerBailout = async (currentCoord) => {
  const endpoint = '/api/bailout';
  const fullUrl = `${API_BASE_URL}${endpoint}`;
  const payload = {
    current_coord: currentCoord, // [lon, lat]
  };

  console.log('[TELEMETRY-API] triggerBailout: Preparing to POST to target URL:', fullUrl);
  console.log('[TELEMETRY-API] triggerBailout: Raw Payload Object Structure:', JSON.stringify(payload, null, 2));

  try {
    const response = await apiClient.post(endpoint, payload);
    console.log('[TELEMETRY-API] triggerBailout: Request succeeded! Status:', response.status);
    return response.data;
  } catch (error) {
    console.error('==================== [triggerBailout TELEMETRY FAILURE DETECTED] ====================');
    console.error('error.message:', error.message);
    console.error('error.code:', error.code);
    if (error.response) {
      console.error('error.response.status (Server Rejected):', error.response.status);
      console.error('error.response.headers:', JSON.stringify(error.response.headers));
      console.error('error.response.data:', JSON.stringify(error.response.data));
    } else {
      console.error('error.response is undefined. The server did not respond or reject with a status code.');
    }
    if (error.request) {
      console.error('error.request is present (Request was sent but no response was received, or blocked by Hermes sandbox)');
      console.error('error.request internal keys:', Object.keys(error.request));
      try {
        console.error('error.request internal metadata stringified:', JSON.stringify(error.request));
      } catch (err) {
        console.error('Failed to stringify error.request:', err.message);
      }
    } else {
      console.error('error.request is undefined.');
    }
    console.error('======================================================================================');
    throw error;
  }
};

export const submitConditionReport = async (reportData) => {
  const endpoint = '/api/community/conditions/report';
  const fullUrl = `${API_BASE_URL}${endpoint}`;
  const payload = {
    reporter_id: reportData.reporterId,
    obstacle_type: reportData.obstacleType,
    latitude: reportData.latitude,
    longitude: reportData.longitude,
  };

  console.log('[TELEMETRY-API] submitConditionReport: Preparing to POST to target URL:', fullUrl);
  console.log('[TELEMETRY-API] submitConditionReport: Raw Payload Object Structure:', JSON.stringify(payload, null, 2));

  try {
    const response = await apiClient.post(endpoint, payload);
    console.log('[TELEMETRY-API] submitConditionReport: Request succeeded! Status:', response.status);
    return response.data;
  } catch (error) {
    console.error('==================== [submitConditionReport TELEMETRY FAILURE DETECTED] ====================');
    console.error('error.message:', error.message);
    console.error('error.code:', error.code);
    if (error.response) {
      console.error('error.response.status (Server Rejected):', error.response.status);
      console.error('error.response.headers:', JSON.stringify(error.response.headers));
      console.error('error.response.data:', JSON.stringify(error.response.data));
    } else {
      console.error('error.response is undefined.');
    }
    if (error.request) {
      console.error('error.request is present (Request was sent but no response was received, or blocked by Hermes sandbox)');
      console.error('error.request internal keys:', Object.keys(error.request));
      try {
        console.error('error.request internal metadata stringified:', JSON.stringify(error.request));
      } catch (err) {
        console.error('Failed to stringify error.request:', err.message);
      }
    } else {
      console.error('error.request is undefined.');
    }
    console.error('============================================================================================');
    throw error;
  }
};

/**
 * UI.11 Emergency SOS API
 * Posts details to satellite offline beacon packet generation API.
 */
export const triggerEmergencyBeacon = async (userId, latitude, longitude, distressMsg) => {
  const endpoint = '/api/emergency/beacon';
  const fullUrl = `${API_BASE_URL}${endpoint}`;
  const payload = {
    user_id: userId,
    latitude: latitude,
    longitude: longitude,
    distress_msg: distressMsg,
  };

  console.log('[TELEMETRY-API] triggerEmergencyBeacon: Preparing to POST to target URL:', fullUrl);
  console.log('[TELEMETRY-API] triggerEmergencyBeacon: Raw Payload Object Structure:', JSON.stringify(payload, null, 2));

  try {
    const response = await apiClient.post(endpoint, payload);
    console.log('[TELEMETRY-API] triggerEmergencyBeacon: Request succeeded! Status:', response.status);
    return response.data;
  } catch (error) {
    console.error('==================== [triggerEmergencyBeacon TELEMETRY FAILURE DETECTED] ====================');
    console.error('error.message:', error.message);
    console.error('error.code:', error.code);
    if (error.response) {
      console.error('error.response.status (Server Rejected):', error.response.status);
      console.error('error.response.headers:', JSON.stringify(error.response.headers));
      console.error('error.response.data:', JSON.stringify(error.response.data));
    } else {
      console.error('error.response is undefined. The server did not respond or reject with a status code.');
    }
    if (error.request) {
      console.error('error.request is present (Request was sent but no response was received, or blocked by Hermes sandbox)');
      console.error('error.request internal keys:', Object.keys(error.request));
      try {
        console.error('error.request internal metadata stringified:', JSON.stringify(error.request));
      } catch (err) {
        console.error('Failed to stringify error.request:', err.message);
      }
    } else {
      console.error('error.request is undefined.');
    }
    console.error('==============================================================================================');
    throw error;
  }
};

export default {
  getRoute,
  triggerBailout,
  submitConditionReport,
  triggerEmergencyBeacon,
};
