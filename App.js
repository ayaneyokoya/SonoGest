import logo from './logo.svg';
import './App.css';
import React, { useState, useEffect, useRef } from 'react';
import Bg from './background.jsx';
import Sono from './SonogestUI.jsx';

function App() {
  return (
    <div>
      <Sono></Sono>
      <Bg></Bg>
    </div>
  );
}

export default App;
