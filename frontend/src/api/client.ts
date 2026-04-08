import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

api.interceptors.response.use(
  (res) => res,
  (error) => {
    const msg = error.response?.data?.detail || error.message;
    console.error('API Error:', msg);
    return Promise.reject(error);
  }
);

export default api;

export const accountApi = {
  list: (params?: any) => api.get('/accounts', { params }),
  create: (data: any) => api.post('/accounts', data),
  get: (id: string) => api.get(`/accounts/${id}`),
  getPassword: (id: string) => api.get(`/accounts/${id}/password`),
  update: (id: string, data: any) => api.put(`/accounts/${id}`, data),
  delete: (id: string) => api.delete(`/accounts/${id}`),
  changePassword: (id: string) => api.post(`/accounts/${id}/change-password`),
  confirmChange: (id: string, newPassword?: string) =>
    api.post(`/accounts/${id}/confirm-change`, null, { params: newPassword ? { new_password: newPassword } : {} }),
  getSupportedProviders: () => api.get('/accounts/providers/supported'),
};

export const historyApi = {
  list: (params?: any) => api.get('/history', { params }),
  count: (params?: any) => api.get('/history/count', { params }),
  getDetail: (id: string) => api.get(`/history/${id}`),
};

export const dashboardApi = {
  get: () => api.get('/dashboard'),
};
