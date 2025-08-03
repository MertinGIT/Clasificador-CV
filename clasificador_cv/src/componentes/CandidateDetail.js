import React, { useState, useEffect } from "react";
import {
  ArrowLeft,
  User,
  Mail,
  Phone,
  Linkedin,
  Github,
  Globe,
  Briefcase,
  Award,
  Languages,
  Star,
  Download,
  MessageCircle,
} from "lucide-react";
import Navbar from "./Navbar";

export default function CandidateDetails({ candidateId, onBack }) {
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (candidateId) {
      fetchCandidateDetails();
    }
  }, [candidateId]);

  const fetchCandidateDetails = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `http://localhost:8000/cv/${candidateId}/analysis`
      );

      if (!response.ok) {
        throw new Error(
          `Error ${response.status}: No se pudieron obtener los detalles`
        );
      }

      const data = await response.json();
      setCandidate(data);
    } catch (error) {
      console.error("Error fetching candidate details:", error);
      setError(error.message);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score >= 80) return "text-green-600 bg-green-100";
    if (score >= 60) return "text-yellow-600 bg-yellow-100";
    if (score >= 40) return "text-orange-600 bg-orange-100";
    return "text-red-600 bg-red-100";
  };

  const getScoreLabel = (score) => {
    if (score >= 80) return "Excelente";
    if (score >= 60) return "Bueno";
    if (score >= 40) return "Regular";
    return "Bajo";
  };

  if (loading) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-gray-800 flex items-center justify-center">
          <div className="text-center text-white">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4"></div>
            <p>Cargando detalles del candidato...</p>
          </div>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-gray-800 flex items-center justify-center">
          <div className="text-center text-white">
            <p className="text-red-400 mb-4">Error: {error}</p>
            <button
              onClick={onBack}
              className="px-4 py-2 bg-gray-600 rounded-md hover:bg-gray-500 transition"
            >
              Volver
            </button>
          </div>
        </div>
      </>
    );
  }

  if (!candidate) {
    return (
      <>
        <Navbar />
        <div className="min-h-screen bg-gray-800 flex items-center justify-center">
          <div className="text-center text-white">
            <p>No se encontraron detalles del candidato</p>
            <button
              onClick={onBack}
              className="mt-4 px-4 py-2 bg-gray-600 rounded-md hover:bg-gray-500 transition"
            >
              Volver
            </button>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-gray-800 text-white p-6">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={onBack}
            className="flex items-center gap-2 text-gray-300 hover:text-white transition mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Volver a candidatos
          </button>

          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold">Perfil del Candidato</h1>
            <div className="flex gap-3">
              <button className="px-4 py-2 bg-blue-600 rounded-md hover:bg-blue-700 transition flex items-center gap-2">
                <Download className="w-4 h-4" />
                Descargar CV
              </button>
              <button className="px-4 py-2 bg-green-600 rounded-md hover:bg-green-700 transition flex items-center gap-2">
                <MessageCircle className="w-4 h-4" />
                Contactar
              </button>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Información Personal */}
          <div className="lg:col-span-1 space-y-6">
            {/* Datos básicos */}
            <div className="bg-white text-black rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <User className="w-6 h-6 text-gray-600" />
                <h2 className="text-xl font-bold">Información Personal</h2>
              </div>

              <div className="space-y-3">
                <div>
                  <h3 className="text-2xl font-bold text-gray-800 mb-1">
                    {candidate.personal_info.nombre || "Nombre no disponible"}
                  </h3>
                  <p className="text-gray-600 text-sm">
                    {candidate.cv_info.filename}
                  </p>
                </div>

                {candidate.personal_info.email && (
                  <div className="flex items-center gap-2">
                    <Mail className="w-4 h-4 text-gray-500" />
                    <a
                      href={`mailto:${candidate.personal_info.email}`}
                      className="text-blue-600 hover:underline"
                    >
                      {candidate.personal_info.email}
                    </a>
                  </div>
                )}

                {candidate.personal_info.telefono && (
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4 text-gray-500" />
                    <a
                      href={`tel:${candidate.personal_info.telefono}`}
                      className="text-blue-600 hover:underline"
                    >
                      {candidate.personal_info.telefono}
                    </a>
                  </div>
                )}
              </div>
            </div>

            {/* Redes sociales */}
            <div className="bg-white text-black rounded-xl p-6">
              <h3 className="font-bold mb-3 flex items-center gap-2">
                <Globe className="w-5 h-5" />
                Enlaces y Redes
              </h3>

              <div className="space-y-2">
                {candidate.personal_info.linkedin && (
                  <a
                    href={candidate.personal_info.linkedin}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-blue-600 hover:underline"
                  >
                    <Linkedin className="w-4 h-4" />
                    LinkedIn
                  </a>
                )}

                {candidate.personal_info.github && (
                  <a
                    href={candidate.personal_info.github}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-gray-800 hover:underline"
                  >
                    <Github className="w-4 h-4" />
                    GitHub
                  </a>
                )}

                {candidate.personal_info.portafolio && (
                  <a
                    href={candidate.personal_info.portafolio}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-purple-600 hover:underline"
                  >
                    <Globe className="w-4 h-4" />
                    Portafolio
                  </a>
                )}

                {!candidate.personal_info.linkedin &&
                  !candidate.personal_info.github &&
                  !candidate.personal_info.portafolio && (
                    <p className="text-gray-500 text-sm">
                      No hay enlaces disponibles
                    </p>
                  )}
              </div>
            </div>

            {/* Score general */}
            <div className="bg-white text-black rounded-xl p-6">
              <div className="flex items-center gap-2 mb-3">
                <Star className="w-5 h-5 text-yellow-500" />
                <h3 className="font-bold">Puntuación General</h3>
              </div>

              <div className="text-center">
                <div
                  className={`inline-flex items-center px-4 py-2 rounded-full font-bold text-lg ${getScoreColor(
                    candidate.cv_info.overall_score
                  )}`}
                >
                  {candidate.cv_info.overall_score || 0}/100
                </div>
                <p className="text-sm text-gray-600 mt-2">
                  {getScoreLabel(candidate.cv_info.overall_score || 0)}
                </p>
              </div>

              {/* Barra de progreso */}
              <div className="mt-4">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{
                      width: `${candidate.cv_info.overall_score || 0}%`,
                    }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          {/* Información Profesional */}
          <div className="lg:col-span-2 space-y-6">
            {/* Experiencia profesional */}
            <div className="bg-white text-black rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <Briefcase className="w-6 h-6 text-gray-600" />
                <h2 className="text-xl font-bold">Información Profesional</h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-gray-700 mb-1">
                    Industria
                  </h4>
                  <p className="text-gray-800">
                    {candidate.professional_info.industria || "No especificada"}
                  </p>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-gray-700 mb-1">Rol</h4>
                  <p className="text-gray-800">
                    {candidate.professional_info.rol || "No especificado"}
                  </p>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-gray-700 mb-1">
                    Puesto/Seniority
                  </h4>
                  <p className="text-gray-800">
                    {candidate.professional_info.puesto || "No especificado"}
                  </p>
                </div>

                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-gray-700 mb-1">
                    Años de Experiencia
                  </h4>
                  <p className="text-gray-800 font-semibold">
                    {candidate.professional_info.anhos_experiencia || 0} años
                  </p>
                </div>
              </div>
            </div>

            {/* Habilidades */}
            <div className="bg-white text-black rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <Award className="w-6 h-6 text-gray-600" />
                <h2 className="text-xl font-bold">Habilidades</h2>
              </div>

              {candidate.skills_and_languages.habilidades &&
              candidate.skills_and_languages.habilidades.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {candidate.skills_and_languages.habilidades.map(
                    (skill, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium"
                      >
                        {skill}
                      </span>
                    )
                  )}
                </div>
              ) : (
                <p className="text-gray-500">
                  No se detectaron habilidades específicas
                </p>
              )}
            </div>

            {/* Idiomas */}
            <div className="bg-white text-black rounded-xl p-6">
              <div className="flex items-center gap-3 mb-4">
                <Languages className="w-6 h-6 text-gray-600" />
                <h2 className="text-xl font-bold">Idiomas</h2>
              </div>

              {candidate.skills_and_languages.idiomas &&
              candidate.skills_and_languages.idiomas.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {candidate.skills_and_languages.idiomas.map(
                    (language, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-green-100 text-green-800 rounded-full text-sm font-medium"
                      >
                        {language}
                      </span>
                    )
                  )}
                </div>
              ) : (
                <p className="text-gray-500">
                  No se detectaron idiomas específicos
                </p>
              )}
            </div>

            {/* Estado del procesamiento */}
            <div className="bg-white text-black rounded-xl p-6">
              <h3 className="font-bold mb-3">Estado del CV</h3>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2">
                  <div
                    className={`w-3 h-3 rounded-full ${
                      candidate.cv_info.processed_status === "completed"
                        ? "bg-green-500"
                        : "bg-yellow-500"
                    }`}
                  ></div>
                  <span className="text-sm">
                    {candidate.cv_info.processed_status === "completed"
                      ? "Procesado completamente"
                      : "En proceso"}
                  </span>
                </div>

                <div className="text-sm text-gray-600">
                  ID: {candidate.cv_info.id}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
