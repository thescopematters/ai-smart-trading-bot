const BASE_URL = import.meta.env.VITE_API_URL || '/api';

const headers = (token, isJson = true) => ({
  ...(isJson && { 'Content-Type': 'application/json' }),
  ...(token && { Authorization: `Bearer ${token}` }),
});

export const api = {
  get: (path, token) =>
    fetch(`${BASE_URL}${path}`, { headers: headers(token, false) }),

  post: (path, body, token) =>
    fetch(`${BASE_URL}${path}`, {
      method: 'POST',
      headers: headers(token),
      body: JSON.stringify(body),
    }),

  postForm: (path, formData, token) =>
    fetch(`${BASE_URL}${path}`, {
      method: 'POST',
      headers: { ...(token && { Authorization: `Bearer ${token}` }) },
      body: formData,
    }),

  postUrlEncoded: (path, body) =>
    fetch(`${BASE_URL}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: body,
    }),

  put: (path, body, token) =>
    fetch(`${BASE_URL}${path}`, {
      method: 'PUT',
      headers: headers(token),
      body: JSON.stringify(body),
    }),

  delete: (path, token) =>
    fetch(`${BASE_URL}${path}`, {
      method: 'DELETE',
      headers: headers(token, false),
    }),
};
