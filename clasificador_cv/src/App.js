import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "./componentes/Login";
import Register from "./componentes/Register";
import UploadCV from "./componentes/UploadCv";
import Navbar from "./componentes/Navbar";
import "./index.css";
import "./App.css";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/"
          element={
            <div className="App">
              <header className="App-header">
                <Login />
              </header>
            </div>
          }
        />

        <Route path="/Register" element={<Register />} />
        <Route path="/UploadCv" element={<UploadCV />} />
        <Route path="/navbar" element={<Navbar />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
