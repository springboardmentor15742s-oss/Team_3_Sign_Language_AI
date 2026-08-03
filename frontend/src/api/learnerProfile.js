import apiClient from './client';

export const learnerProfileApi = {
  getProfile: async () => {
    const response = await apiClient.get('/learner-profiles/me');
    return response.data;
  },

  updateProfile: async (payload) => {
    const response = await apiClient.put('/learner-profiles/me', payload);
    return response.data;
  },

  updateProgress: async (payload) => {
    const response = await apiClient.patch('/learner-profiles/me/progress', payload);
    return response.data;
  },

  uploadPicture: async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post('/learner-profiles/me/picture', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },
};
