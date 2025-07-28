import React, { useState } from "react";
import { MessageCircle } from "lucide-react";
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

export default function ClasificadorCV() {
  const [busqueda, setBusqueda] = useState("");
  const [filtros, setFiltros] = useState({
    area: "",
    habilidades: [],
    experiencia: "",
    idiomas: "",
  });

  const [chatInput, setChatInput] = useState("");
  const [chatResponse, setChatResponse] = useState("");
  const [loading, setLoading] = useState(false);

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

  const handleBuscar = async () => {
    const prompt = construirPromptDesdeFiltros();
    await consultarLLM(prompt);
  };

  const consultarLLM = async (texto) => {
    try {
      setLoading(true);
      const res = await fetch(
        `http://localhost:8000/ask?query=${encodeURIComponent(texto)}`
      );
      const data = await res.json();
      setChatResponse(data.answer);
    } catch (err) {
      setChatResponse("❌ Error al consultar al modelo.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleChat = async () => {
    if (!chatInput.trim()) return;
    await consultarLLM(chatInput);
  };

  return (
    <>
      <Navbar />
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 min-h-screen bg-gray-800 text-white">
        <div className="bg-white text-black rounded-xl shadow-lg p-6 space-y-4">
          <h2 className="text-xl font-bold">Búsqueda avanzada</h2>

          <textarea
            placeholder="Ej: Busco alguien con experiencia en ventas, atención al cliente y buen nivel de inglés..."
            value={busqueda}
            onChange={(e) => setBusqueda(e.target.value)}
            className="w-full h-24 p-3 border rounded-md resize-none"
          />

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <select
              value={filtros.area}
              onChange={(e) => setFiltros({ ...filtros, area: e.target.value })}
              className="border p-2 rounded-md"
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
              className="border p-2 rounded-md"
            />

            <input
              placeholder="Idiomas requeridos"
              value={filtros.idiomas}
              onChange={(e) =>
                setFiltros({ ...filtros, idiomas: e.target.value })
              }
              className="border p-2 rounded-md md:col-span-2"
            />
          </div>

          <div>
            <p className="font-medium">Habilidades clave:</p>
            <div className="flex flex-wrap gap-2 mt-2">
              {habilidades.map((skill) => (
                <span
                  key={skill}
                  className={`px-3 py-1 rounded-full cursor-pointer border text-sm transition ${
                    filtros.habilidades.includes(skill)
                      ? "bg-black text-white"
                      : "bg-white text-black"
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
            className="w-full py-2 mt-4 rounded-md bg-black text-white hover:bg-gray-900 transition"
          >
            Buscar candidatos ideales
          </button>
        </div>

        <div className="bg-white text-black rounded-xl shadow-lg p-6 space-y-4">
          <h2 className="text-xl font-bold flex items-center gap-2">
            <MessageCircle className="w-5 h-5" /> Reclutador (Chat)
          </h2>

          <textarea
            placeholder="Describe el perfil que buscas (ej: Necesito un profesional con enfoque comercial, buen trato con clientes y manejo de CRM)..."
            rows={6}
            className="w-full p-3 border rounded-md resize-none"
          />

          <button className="w-full py-2 mt-2 rounded-md bg-gray-900 text-white hover:bg-black transition">
            Consultar
          </button>
        </div>
      </div>
    </>
  );
}
