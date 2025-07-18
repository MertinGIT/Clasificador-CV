import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from './componentes/Login';
import Register from './componentes/Register';
import './App.css';

function App() {
  return (
  <BrowserRouter>
  <Routes>  
    <Route path="/" element={(
      <div className="App">
      <header className="App-header">
          <Login />
      </header>
    </div>

    )}/>
    
    <Route path="/Register" element={<Register/>}/>

  </Routes>

  </BrowserRouter>
  );
}

export default App;
