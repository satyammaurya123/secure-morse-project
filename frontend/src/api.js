import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000',
});

// Request interceptor to add the access token to headers
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access');
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to attempt token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refresh');
      if (refreshToken) {
        try {
          const res = await axios.post(`${import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'}/auth/token/refresh/`, {
            refresh: refreshToken
          });
          localStorage.setItem('access', res.data.access);
          api.defaults.headers.common['Authorization'] = `Bearer ${res.data.access}`;
          return api(originalRequest);
          // } catch (refreshError) {
        } catch (/* refreshError */ _error) {
          // Refresh token is expired or invalid
          localStorage.removeItem('access');
          localStorage.removeItem('refresh');
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export const checkAuthStatus = () => api.get('/auth/status/');
export const login = (credentials) => api.post('/auth/login/', credentials);
export const signup = (userData) => api.post('/auth/signup/', userData);
export const logout = () => api.post('/auth/logout/');

export const encodeImage = (formData) => api.post('/api/encode/', formData);

export const decodeImage = (formData) => api.post('/api/decode/', formData);

export const registerAudioStego = (data) => api.post('/api/audio-stego/register/', data);

export const verifyAudioStego = (formData) => api.post('/api/audio-stego/verify/', formData);

export default api;
