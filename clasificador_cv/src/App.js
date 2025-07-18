import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from './componentes/Login';
import Register from './componentes/Register';
import './App.css';

function App() {
  return (
  <BrowserRouter>
  <Routes>  
    <div className="App">
      <header className="App-header">
          <Login />
      </header>
    </div>
    <Route path="/register" element={<Register/>}/>

  </Routes>

  </BrowserRouter>
  );
}

export default App;
