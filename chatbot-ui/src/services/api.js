const BASE_URL = import.meta.env.VITE_API_URL || '';

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

  delete: (path, token) =>
    fetch(`${BASE_URL}${path}`, {
      method: 'DELETE',
      headers: headers(token, false),
    }),
};