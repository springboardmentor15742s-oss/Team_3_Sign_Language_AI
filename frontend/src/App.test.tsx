import React from 'react';
import { render, screen } from '@testing-library/react';
import App from './App';

test('redirects unauthenticated users to the login page', () => {
  render(<App />);
  expect(screen.getByRole('heading', { name: /sign language platform/i })).toBeInTheDocument();
  expect(screen.getByRole('tab', { name: /log in/i })).toBeInTheDocument();
});
