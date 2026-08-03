export const formatApiError = (error) => {
  if (!error) return 'An unexpected error occurred.';

  if (error.response) {
    const data = error.response.data;
    if (data && data.detail) {
      if (typeof data.detail === 'string') {
        return data.detail;
      }
      if (Array.isArray(data.detail)) {
        return data.detail.map((err) => `${err.loc?.slice(-1)[0] || 'field'}: ${err.msg}`).join(', ');
      }
    }
    return `Server Error (${error.response.status}): ${error.response.statusText}`;
  }

  if (error.request) {
    return 'Unable to reach the server. Please check your network connection or server status.';
  }

  return error.message || 'An error occurred while processing your request.';
};
