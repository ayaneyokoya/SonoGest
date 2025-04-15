// Correct for React 18
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// Get the container to mount your app
const container = document.getElementById('root');

// Create a root.
const root = ReactDOM.createRoot(container);

// Initial render: Render your app
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
