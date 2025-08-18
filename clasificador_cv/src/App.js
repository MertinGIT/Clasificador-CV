import { BrowserRouter, Routes, Route } from "react-router-dom";
import { useState } from "react";
import Login from "./componentes/Login";
import Register from "./componentes/Register";
import UploadCV from "./componentes/UploadCv";
import Sidebar from "./componentes/Sidebar";
import Navbar from "./componentes/Navbar";
import ChatCv from "./componentes/ChatCv";
import UploadDoc from "./componentes/UploadDoc";
import CandidateDetail from "./componentes/CandidateDetail";
import "./index.css";
import "./App.css";

function App() {
  // 🔹 estados necesarios
  const [currentView, setCurrentView] = useState("search");
  const [selectedCandidateId, setSelectedCandidateId] = useState(null);

  const handleCandidateSelect = (candidateId) => {
    console.log("Candidato seleccionado:", candidateId);
    setSelectedCandidateId(candidateId);
    setCurrentView("details");
  };

  const handleBackToSearch = () => {
    setCurrentView("search");
    setSelectedCandidateId(null);
  };

  return (
    <div className="App">
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
          {/* 🔹 Pasamos handleCandidateSelect a ChatCv */}
          <Route
            path="/ChatCv"
            element={<ChatCv onCandidateSelect={handleCandidateSelect} />}
          />
          <Route path="/Navbar" element={<Navbar />} />
          <Route path="/UploadDoc" element={<UploadDoc />} />
          <Route
            path="/CandidateDetail"
            element={
              <CandidateDetail
                candidateId={selectedCandidateId}
                onBack={handleBackToSearch}
              />
            }
          />
        </Routes>

        {/* 🔹 Vista dinámica fuera del router */}
        {currentView === "search" && (
          <ChatCv onCandidateSelect={handleCandidateSelect} />
        )}

        {currentView === "details" && (
          <CandidateDetail
            candidateId={selectedCandidateId}
            onBack={handleBackToSearch}
          />
        )}
      </BrowserRouter>
    </div>
  );
}

export default App;
