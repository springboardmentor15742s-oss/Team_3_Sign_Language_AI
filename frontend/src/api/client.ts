import axios from 'axios';

const client = axios.create({
  baseURL: 'http://localhost:8000',
  // Without this, axios waits indefinitely on a stuck connection — a
  // request would never resolve or reject, so a try/finally around it
  // would never run either. This guarantees it eventually fails loudly.
  timeout: 20000,
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export default client;
