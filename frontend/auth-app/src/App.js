import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Register from './Register'; 
import Login from './Login';
import ProtectedPage from './Protected';


function App() {
  
  return (
    <Router>
      <Routes>
      <Route path="/register" element={<Register />} />  
      <Route path="/" element={<Login />} />
      <Route path="/protected" element={<ProtectedPage />} />
      </Routes>
    </Router>
  );
}

export default App;
