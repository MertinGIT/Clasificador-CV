import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "./componentes/Login";
import Register from "./componentes/Register";
import UploadCV from "./componentes/UploadCv";
import Sidebar from "./componentes/Sidebar";
import Navbar from "./componentes/Navbar";
import ChatCv from "./componentes/ChatCv";
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
        <Route path="/Sidebar" element={<Sidebar />} />
        <Route path="/ChatCv" element={<ChatCv />} />
        <Route path="/Navbar" element={<Navbar />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
