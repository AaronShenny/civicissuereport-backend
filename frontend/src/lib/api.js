import { supabase } from './supabase';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';

async function getHeaders(isFormData = false) {
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  
  const headers = {};
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  if (!isFormData) {
    headers['Content-Type'] = 'application/json';
  }
  return headers;
}

async function request(endpoint, options = {}) {
  const isFormData = options.body instanceof FormData;
  const headers = await getHeaders(isFormData);
  
  const config = {
    ...options,
    headers: {
      ...headers,
      ...options.headers,
    },
  };

  const url = `${API_BASE_URL}${endpoint}`;
  
  let response;
  try {
    response = await fetch(url, config);
  } catch (networkError) {
    console.error(`[API] Network Error connecting to ${endpoint}:`, networkError);
    throw new Error(`Network Error: Unable to connect to ${endpoint}`);
  }

  if (!response.ok) {
    let errorData;
    let detailStr = response.statusText;
    try {
      errorData = await response.json();
      detailStr = errorData.detail || JSON.stringify(errorData);
    } catch {
      errorData = { detail: response.statusText };
    }
    
    // Construct a highly visible error message for debugging
    const errorMessage = `API Error ${response.status} at ${endpoint}: ${detailStr}`;
    console.error(`[API ERROR]`, { status: response.status, endpoint, errorData });
    
    const error = new Error(errorMessage);
    error.status = response.status;
    error.data = errorData;
    throw error;
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return null;
  }

  return response.json();
}

export const api = {
  get: (endpoint, options) => request(endpoint, { method: 'GET', ...options }),
  post: (endpoint, body, options) => request(endpoint, { method: 'POST', body: body instanceof FormData ? body : JSON.stringify(body), ...options }),
  put: (endpoint, body, options) => request(endpoint, { method: 'PUT', body: body instanceof FormData ? body : JSON.stringify(body), ...options }),
  patch: (endpoint, body, options) => request(endpoint, { method: 'PATCH', body: body instanceof FormData ? body : JSON.stringify(body), ...options }),
  delete: (endpoint, options) => request(endpoint, { method: 'DELETE', ...options }),
};
