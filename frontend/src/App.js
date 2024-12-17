// src/App.js

import React from 'react';
import DataLabeler from './components/DataLabeler';
import './App.css';  // Falls du globale Stile hast

function App() {
  return (
    <div className="App">
      <header>
        <h1>Sensor Data Labeling</h1>
      </header>
      <main>
        <DataLabeler />
      </main>
    </div>
  );
}

export default App;
