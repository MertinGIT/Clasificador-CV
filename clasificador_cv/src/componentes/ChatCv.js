import React, { useState } from "react";
import { MessageCircle, Search, Users, Filter, ArrowRight } from "lucide-react";
import Navbar from "./Navbar";

const areas = [
  "Administración",
  "Marketing",
  "Ingeniería",
  "Salud",
  "Educación",
  "Tecnología",
  "Logística",
  "Legal",
  "Ventas",
  "Diseño",
];

const habilidades = [
  "Liderazgo",
  "Trabajo en equipo",
  "Atención al cliente",
  "Resolución de problemas",
  "Manejo de Excel",
  "Inglés",
  "Comunicación",
  "Análisis de datos",
];

export default function ClasificadorCV({ onCandidateSelect }) {
  const [busqueda, setBusqueda] = useState("");
  const [filtros, setFiltros] = useState({
    area: "",
    habilidades: [],
    experiencia: "",
    idiomas: "",
  });

  const [chatInput, setChatInput] = useState("");
  const [chatResponse, setChatResponse] = useState("");
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingChat, setLoadingChat] = useState(false);
  const [activeTab, setActiveTab] = useState("search"); // "search" o "candidates"

  const toggleHabilidad = (skill) => {
    setFiltros((prev) => {
      const nuevas = prev.habilidades.includes(skill)
        ? prev.habilidades.filter((h) => h !== skill)
        : [...prev.habilidades, skill];
      return { ...prev, habilidades: nuevas };
    });
  };

  const construirPromptDesdeFiltros = () => {
    return `
Busco un perfil profesional en el área de ${
      filtros.area || "cualquier área"
    } con aproximadamente ${
      filtros.experiencia || "alguna"
    } años de experiencia. 
Debe tener habilidades como ${
      filtros.habilidades.join(", ") || "habilidades generales"
    } y manejar los siguientes idiomas: ${filtros.idiomas || "no especificado"}.
${busqueda ? `Descripción adicional: ${busqueda}` : ""}
    `.trim();
  };

  // BÚSQUEDA SEMÁNTICA CON EMBEDDINGS
  const handleBuscar = async () => {
    try {
      setLoading(true);
      const query = construirPromptDesdeFiltros();

      // Construir parámetros de consulta
      const params = new URLSearchParams({
        query: query,
        n_results: "10",
        use_embeddings: "true",
      });

      // Agregar filtros opcionales
      if (filtros.area) {
        // Mapear área del frontend a industria del backend
        const industryMap = {
          Tecnología: "Tecnología",
          Salud: "Salud",
          Educación: "Educación",
          Marketing: "Marketing",
          Ventas: "Ventas",
          Administración: "Administración",
          Legal: "Legal",
          Ingeniería: "Ingeniería",
          Logística: "Logística",
          Diseño: "Diseño",
        };

        if (industryMap[filtros.area]) {
          params.append("industry_filter", industryMap[filtros.area]);
        }
      }

      // Filtro por score mínimo basado en experiencia
      if (filtros.experiencia) {
        const exp = parseInt(filtros.experiencia);
        if (exp >= 5) {
          params.append("min_score", "70");
        } else if (exp >= 2) {
          params.append("min_score", "50");
        } else {
          params.append("min_score", "30");
        }
      }

      const response = await fetch(`http://localhost:8000/search?${params}`);

      if (!response.ok) {
        throw new Error(`Error ${response.status}: ${await response.text()}`);
      }

      const data = await response.json();
      setSearchResults(data.matches || []);

      if (data.matches && data.matches.length > 0) {
        setActiveTab("candidates");
      }
    } catch (error) {
      console.error("Error en búsqueda:", error);
      setSearchResults([]);
      alert(`Error al buscar candidatos: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // CONSULTA CON LLM - MODIFICADA para buscar candidatos también
  const consultarLLM = async (texto) => {
    try {
      setLoadingChat(true);

      // Primero hacemos la consulta al LLM para obtener la respuesta
      const chatParams = new URLSearchParams({
        query: texto,
      });

      // Agregar filtros de contexto si están disponibles
      if (filtros.area) {
        chatParams.append("industry_filter", filtros.area);
      }

      if (filtros.experiencia) {
        const exp = parseInt(filtros.experiencia);
        if (exp >= 3) {
          chatParams.append("min_score", "60");
        }
      }

      const chatResponse = await fetch(
        `http://localhost:8000/ask?${chatParams}`
      );

      if (!chatResponse.ok) {
        throw new Error(
          `Error ${chatResponse.status}: ${await chatResponse.text()}`
        );
      }

      const chatData = await chatResponse.json();
      setChatResponse(chatData.answer || "No se recibió respuesta del modelo.");

      // Ahora también buscamos candidatos relacionados
      const searchParams = new URLSearchParams({
        query: texto,
        n_results: "10",
        use_embeddings: "true",
      });

      // Aplicar los mismos filtros que en la búsqueda avanzada
      if (filtros.area) {
        const industryMap = {
          Tecnología: "Tecnología",
          Salud: "Salud",
          Educación: "Educación",
          Marketing: "Marketing",
          Ventas: "Ventas",
          Administración: "Administración",
          Legal: "Legal",
          Ingeniería: "Ingeniería",
          Logística: "Logística",
          Diseño: "Diseño",
        };

        if (industryMap[filtros.area]) {
          searchParams.append("industry_filter", industryMap[filtros.area]);
        }
      }

      if (filtros.experiencia) {
        const exp = parseInt(filtros.experiencia);
        if (exp >= 5) {
          searchParams.append("min_score", "70");
        } else if (exp >= 2) {
          searchParams.append("min_score", "50");
        } else {
          searchParams.append("min_score", "30");
        }
      }

      const searchResponse = await fetch(
        `http://localhost:8000/search?${searchParams}`
      );

      if (searchResponse.ok) {
        const searchData = await searchResponse.json();
        setSearchResults(searchData.matches || []);

        // Cambiar a la pestaña de candidatos si hay resultados
        if (searchData.matches && searchData.matches.length > 0) {
          setActiveTab("candidates");
        }
      }
    } catch (error) {
      console.error("Error en chat:", error);
      setChatResponse(`❌ Error al consultar al modelo: ${error.message}`);
    } finally {
      setLoadingChat(false);
    }
  };

  const handleBuscarConFiltros = async () => {
    const prompt = construirPromptDesdeFiltros();
    await consultarLLM(prompt);
  };

  const handleChat = async () => {
    if (!chatInput.trim()) return;
    await consultarLLM(chatInput);
  };

  // Función para obtener detalles completos de un candidato
  const verDetallesCandidato = async (candidate) => {
    // Intentar diferentes campos para el ID
    const possibleIds = [
      candidate.cv_id,
      candidate.id,
      candidate.document_id,
      candidate.file_id,
    ].filter(Boolean);

    console.log("Candidato completo:", candidate);
    console.log("IDs posibles:", possibleIds);

    if (onCandidateSelect) {
      // Probar con el primer ID válido
      const candidateId = possibleIds[0];
      if (candidateId) {
        onCandidateSelect(candidateId);
      } else {
        alert("No se pudo determinar el ID del candidato");
      }
    } else {
      // Fallback: intentar con cada ID hasta que uno funcione
      let success = false;

      for (const id of possibleIds) {
        try {
          console.log(`Intentando con ID: ${id}`);
          const response = await fetch(
            `http://localhost:8000/cv/${id}/analysis`
          );

          if (response.ok) {
            const data = await response.json();
            console.log("Detalles del candidato:", data);
            alert(
              `Candidato: ${data.personal_info.nombre}\nEmail: ${data.personal_info.email}\nScore: ${data.cv_info.overall_score}`
            );
            success = true;
            break;
          } else {
            console.log(`ID ${id} no funcionó: ${response.status}`);
          }
        } catch (error) {
          console.error(`Error con ID ${id}:`, error);
        }
      }

      if (!success) {
        alert(
          "No se pudieron obtener los detalles del candidato. Revisa la consola para más información."
        );
      }
    }
  };

  const MatchStrengthBadge = ({ strength, similarity }) => {
    const colors = {
      Excelente: "bg-green-500",
      Bueno: "bg-blue-500",
      Regular: "bg-yellow-500",
      Bajo: "bg-red-500",
    };

    return (
      <span
        className={`px-2 py-1 rounded-full text-xs text-white ${
          colors[strength] || "bg-gray-500"
        }`}
      >
        {strength} ({similarity || "N/A"})
      </span>
    );
  };

  return (
    <>
      <Navbar />
      <div className="min-h-screen bg-gray-800 text-white p-6">
        {/* Tabs */}
        <div className="flex mb-6 bg-gray-700 rounded-lg p-1">
          <button
            onClick={() => setActiveTab("search")}
            className={`flex-1 py-2 px-4 rounded-md flex items-center justify-center gap-2 transition ${
              activeTab === "search"
                ? "bg-white text-black"
                : "text-white hover:bg-gray-600"
            }`}
          >
            <Search className="w-4 h-4" />
            Búsqueda
          </button>
          <button
            onClick={() => setActiveTab("candidates")}
            className={`flex-1 py-2 px-4 rounded-md flex items-center justify-center gap-2 transition ${
              activeTab === "candidates"
                ? "bg-white text-black"
                : "text-white hover:bg-gray-600"
            }`}
          >
            <Users className="w-4 h-4" />
            Candidatos ({searchResults.length})
          </button>
        </div>

        {/* Contenido según tab activa */}
        {activeTab === "search" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Panel de Búsqueda Avanzada */}
            <div className="bg-white text-black rounded-xl shadow-lg p-6 space-y-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <Filter className="w-5 h-5" />
                Búsqueda avanzada
              </h2>

              <textarea
                placeholder="Ej: Busco alguien con experiencia en ventas, atención al cliente y buen nivel de inglés..."
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
                className="w-full h-24 p-3 border rounded-md resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <select
                  value={filtros.area}
                  onChange={(e) =>
                    setFiltros({ ...filtros, area: e.target.value })
                  }
                  className="border p-2 rounded-md focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Área profesional</option>
                  {areas.map((a) => (
                    <option key={a} value={a}>
                      {a}
                    </option>
                  ))}
                </select>

                <input
                  type="number"
                  placeholder="Años de experiencia"
                  value={filtros.experiencia}
                  onChange={(e) =>
                    setFiltros({ ...filtros, experiencia: e.target.value })
                  }
                  className="border p-2 rounded-md focus:ring-2 focus:ring-blue-500"
                />

                <input
                  placeholder="Idiomas requeridos"
                  value={filtros.idiomas}
                  onChange={(e) =>
                    setFiltros({ ...filtros, idiomas: e.target.value })
                  }
                  className="border p-2 rounded-md md:col-span-2 focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <p className="font-medium mb-2">Habilidades clave:</p>
                <div className="flex flex-wrap gap-2">
                  {habilidades.map((skill) => (
                    <span
                      key={skill}
                      className={`px-3 py-1 rounded-full cursor-pointer border text-sm transition ${
                        filtros.habilidades.includes(skill)
                          ? "bg-black text-white"
                          : "bg-white text-black hover:bg-gray-100"
                      }`}
                      onClick={() => toggleHabilidad(skill)}
                    >
                      {skill}
                    </span>
                  ))}
                </div>
              </div>

              <button
                onClick={handleBuscar}
                disabled={loading}
                className="w-full py-3 mt-4 rounded-md bg-black text-white hover:bg-gray-900 transition disabled:opacity-50 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Buscando...
                  </>
                ) : (
                  <>
                    <Search className="w-4 h-4" />
                    Buscar candidatos ideales
                  </>
                )}
              </button>
            </div>

            {/* Panel de Chat con LLM */}
            <div className="bg-white text-black rounded-xl shadow-lg p-6 space-y-4">
              <h2 className="text-xl font-bold flex items-center gap-2">
                <MessageCircle className="w-5 h-5" />
                Consulta al Reclutador IA
              </h2>

              <textarea
                placeholder="Describe el perfil que buscas (ej: Necesito un profesional con enfoque comercial, buen trato con clientes y manejo de CRM)..."
                value={chatInput}
                onChange={(e) => setChatInput(e.target.value)}
                rows={6}
                className="w-full p-3 border rounded-md resize-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              />

              <div className="flex gap-2">
                <button
                  onClick={handleChat}
                  disabled={loadingChat || !chatInput.trim()}
                  className="flex-1 py-2 rounded-md bg-gray-900 text-white hover:bg-black transition disabled:opacity-50 flex items-center justify-center gap-2"
                >
                  {loadingChat ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Consultando...
                    </>
                  ) : (
                    <>
                      <MessageCircle className="w-4 h-4" />
                      Consultar IA
                    </>
                  )}
                </button>

                <button
                  onClick={handleBuscarConFiltros}
                  disabled={loadingChat}
                  className="px-4 py-2 rounded-md bg-blue-600 text-white hover:bg-blue-700 transition disabled:opacity-50"
                >
                  Usar filtros
                </button>
              </div>

              {/* Respuesta del Chat - Solo se muestra si no hay candidatos o si hay respuesta */}
              {chatResponse && searchResults.length === 0 && (
                <div className="mt-4 p-4 bg-gray-50 rounded-md border">
                  <h3 className="font-medium mb-2">
                    Recomendación del Reclutador IA:
                  </h3>
                  <div className="text-sm text-gray-700 whitespace-pre-wrap">
                    {chatResponse}
                  </div>
                </div>
              )}

              {/* Mensaje cuando hay candidatos encontrados */}
              {chatResponse && searchResults.length > 0 && (
                <div className="mt-4 p-4 bg-blue-50 rounded-md border border-blue-200">
                  <p className="text-sm text-blue-800">
                    ✅ Consulta procesada. Se encontraron {searchResults.length}{" "}
                    candidatos. Ve a la pestaña "Candidatos" para verlos.
                  </p>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Panel de Candidatos */}
        {activeTab === "candidates" && (
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold">Candidatos Encontrados</h2>
              <div className="flex gap-3">
                {/* Mostrar respuesta del chat si existe */}
                {chatResponse && (
                  <div className="text-sm text-gray-300 max-w-md">
                    Recomendación IA disponible
                  </div>
                )}
                <button
                  onClick={() => setActiveTab("search")}
                  className="px-4 py-2 bg-gray-600 rounded-md hover:bg-gray-500 transition"
                >
                  Nueva búsqueda
                </button>
              </div>
            </div>

            {/* Respuesta del Chat en la pestaña de candidatos */}
            {chatResponse && (
              <div className="bg-white text-black rounded-xl p-4 mb-4">
                <h3 className="font-medium mb-2">
                  Recomendación del Reclutador IA:
                </h3>
                <div className="text-sm text-gray-700 whitespace-pre-wrap">
                  {chatResponse}
                </div>
              </div>
            )}

            {searchResults.length === 0 ? (
              <div className="text-center py-12 bg-gray-700 rounded-xl">
                <Users className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                <p className="text-gray-300">No hay candidatos para mostrar</p>
                <p className="text-sm text-gray-400 mt-2">
                  Realiza una búsqueda para ver resultados
                </p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {searchResults.map((candidate, index) => (
                  <div
                    key={candidate.cv_id || index}
                    className="bg-white text-black rounded-lg p-6 shadow-lg hover:shadow-xl transition-shadow"
                  >
                    {/* Header del candidato */}
                    <div className="flex justify-between items-start mb-3">
                      <div>
                        <h3 className="font-bold text-lg text-gray-800">
                          {candidate.nombre || "Candidato"}
                        </h3>
                        <p className="text-sm text-gray-600">
                          {candidate.filename}
                        </p>
                      </div>
                      <MatchStrengthBadge
                        strength={candidate.match_strength}
                        similarity={candidate.similarity}
                      />
                    </div>

                    {/* Información del candidato */}
                    <div className="space-y-2 mb-4">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Rol:</span>
                        <span className="text-sm font-medium">
                          {candidate.role || "N/A"}
                        </span>
                      </div>

                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">
                          Experiencia:
                        </span>
                        <span className="text-sm font-medium">
                          {candidate.experience || "N/A"}
                        </span>
                      </div>

                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">
                          Industria:
                        </span>
                        <span className="text-sm font-medium">
                          {candidate.industry || "N/A"}
                        </span>
                      </div>

                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">Score:</span>
                        <span className="text-sm font-medium">
                          {candidate.score || "N/A"}/100
                        </span>
                      </div>

                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">
                          Seniority:
                        </span>
                        <span className="text-sm font-medium">
                          {candidate.seniority || "N/A"}
                        </span>
                      </div>
                    </div>

                    {/* Preview del contenido */}
                    {candidate.preview && (
                      <div className="mb-4">
                        <p className="text-xs text-gray-500 mb-1">
                          Vista previa:
                        </p>
                        <p className="text-xs text-gray-700 line-clamp-3">
                          {candidate.preview}
                        </p>
                      </div>
                    )}

                    {/* Botón de acción */}
                    <button
                      onClick={() => verDetallesCandidato(candidate.cv_id)}
                      className="w-full py-2 px-4 bg-black text-white rounded-md hover:bg-gray-800 transition flex items-center justify-center gap-2"
                    >
                      Ver detalles completos
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}
