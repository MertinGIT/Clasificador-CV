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
  TrendingUp,
  Target,
  Clock,
  MapPin,
  GraduationCap,
  Zap,
  BarChart3,
  PieChart,
  Activity,
} from "lucide-react";

// Componente de gráfico circular simple
const CircularProgress = ({
  percentage,
  size = 120,
  strokeWidth = 8,
  color = "#3B82F6",
}) => {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div className="relative inline-flex items-center justify-center">
      <svg width={size} height={size} className="transform -rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke="#E5E7EB"
          strokeWidth={strokeWidth}
          fill="transparent"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          stroke={color}
          strokeWidth={strokeWidth}
          fill="transparent"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-in-out"
        />
      </svg>
      <div className="absolute text-center">
        <div className="text-2xl font-bold text-gray-800">{percentage}</div>
        <div className="text-xs text-gray-600">SCORE</div>
      </div>
    </div>
  );
};

// Componente de barra de habilidades
const SkillBar = ({ skill, level, color = "bg-blue-500" }) => {
  return (
    <div className="mb-3">
      <div className="flex justify-between mb-1">
        <span className="text-sm font-medium text-gray-700">{skill}</span>
        <span className="text-sm text-gray-500">{level}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={`${color} h-2 rounded-full transition-all duration-1000 ease-out`}
          style={{ width: `${level}%` }}
        ></div>
      </div>
    </div>
  );
};

// Componente de métrica
const MetricCard = ({
  icon: Icon,
  title,
  value,
  subtitle,
  color = "text-blue-600",
}) => {
  return (
    <div className="bg-white p-4 rounded-lg border border-gray-200 hover:shadow-md transition-shadow">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-gray-600 mb-1">{title}</p>
          <p className={`text-2xl font-bold ${color}`}>{value}</p>
          {subtitle && <p className="text-xs text-gray-500 mt-1">{subtitle}</p>}
        </div>
        <Icon className={`w-8 h-8 ${color}`} />
      </div>
    </div>
  );
};

export default function CandidateDetails({ candidateId, onBack }) {
  const [candidate, setCandidate] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");

  useEffect(() => {
    if (candidateId) {
      fetchCandidateDetails();
    }
  }, [candidateId]);

  const fetchCandidateDetails = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `http://localhost:8000/cv/${candidateId}/analisis-completo`
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
    if (score >= 80) return "#10B981"; // Verde
    if (score >= 60) return "#F59E0B"; // Amarillo
    if (score >= 40) return "#F97316"; // Naranja
    return "#EF4444"; // Rojo
  };

  const getScoreLabel = (score) => {
    if (score >= 80) return "Excelente";
    if (score >= 60) return "Bueno";
    if (score >= 40) return "Regular";
    return "Bajo";
  };

  // Función para generar datos simulados de habilidades con niveles
  const getSkillsWithLevels = (skills) => {
    if (!skills || !Array.isArray(skills)) return [];

    return skills.map((skill, index) => ({
      name: skill,
      level: Math.floor(Math.random() * 40) + 60, // Entre 60-100 para candidatos cualificados
    }));
  };

  // Calcular métricas derivadas
  const calculateMetrics = () => {
    if (!candidate) return {};

    const experience = candidate.professional_info?.anhos_experiencia || 0;
    const skills = candidate.skills_and_languages?.habilidades || [];
    const languages = candidate.skills_and_languages?.idiomas || [];
    const score = candidate.cv_info?.overall_score || 0;

    return {
      experienceLevel:
        experience >= 5 ? "Senior" : experience >= 2 ? "Mid" : "Junior",
      skillCount: skills.length,
      languageCount: languages.length,
      profileCompleteness: Math.min(
        100,
        (candidate.personal_info?.nombre ? 20 : 0) +
          (candidate.personal_info?.email ? 20 : 0) +
          (candidate.professional_info?.industria ? 15 : 0) +
          (candidate.professional_info?.rol ? 15 : 0) +
          (skills.length > 0 ? 20 : 0) +
          (languages.length > 0 ? 10 : 0)
      ),
      marketValue:
        score >= 80
          ? "Alto"
          : score >= 60
          ? "Medio-Alto"
          : score >= 40
          ? "Medio"
          : "Bajo",
    };
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Cargando perfil del candidato...</p>
        </div>
      </div>
    );
  }

  if (error || !candidate) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">
            {error || "No se encontraron detalles del candidato"}
          </p>
          <button
            onClick={onBack}
            className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 transition"
          >
            Volver
          </button>
        </div>
      </div>
    );
  }

  const metrics = calculateMetrics();
  const skillsWithLevels = getSkillsWithLevels(
    candidate.skills_and_languages?.habilidades
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <button
                onClick={onBack}
                className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition"
              >
                <ArrowLeft className="w-5 h-5" />
                Volver
              </button>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  {candidate.personal_info?.nombre ||
                    candidate.classic_data?.nombre ||
                    "Candidato"}
                </h1>
                <p className="text-sm text-gray-500">
                  {candidate.professional_info?.rol || "Profesional"} •
                  {candidate.professional_info?.industria || "Sin especificar"}
                </p>
              </div>
            </div>

            <div className="flex gap-3">
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition flex items-center gap-2">
                <Download className="w-4 h-4" />
                Descargar CV
              </button>
              <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition flex items-center gap-2">
                <MessageCircle className="w-4 h-4" />
                Contactar
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex space-x-8">
            {[
              { id: "overview", label: "Resumen", icon: Activity },
              { id: "skills", label: "Habilidades", icon: Award },
              { id: "experience", label: "Experiencia", icon: Briefcase },
              { id: "contact", label: "Contacto", icon: User },
            ].map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => setActiveTab(id)}
                className={`flex items-center gap-2 py-4 px-2 border-b-2 font-medium text-sm transition ${
                  activeTab === id
                    ? "border-blue-500 text-blue-600"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                }`}
              >
                <Icon className="w-4 h-4" />
                {label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Overview Tab */}
        {activeTab === "overview" && (
          <div className="space-y-8">
            {/* Métricas principales */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <MetricCard
                icon={Star}
                title="Puntuación General"
                value={`${candidate.cv_info?.overall_score || 0}/100`}
                subtitle={getScoreLabel(candidate.cv_info?.overall_score || 0)}
                color="text-blue-600"
              />
              <MetricCard
                icon={Clock}
                title="Experiencia"
                value={`${
                  candidate.professional_info?.anhos_experiencia || 0
                } años`}
                subtitle={metrics.experienceLevel}
                color="text-green-600"
              />
              <MetricCard
                icon={Award}
                title="Habilidades"
                value={metrics.skillCount}
                subtitle="Detectadas"
                color="text-purple-600"
              />
              <MetricCard
                icon={TrendingUp}
                title="Valor de Mercado"
                value={metrics.marketValue}
                subtitle={`${metrics.profileCompleteness}% completo`}
                color="text-orange-600"
              />
            </div>

            {/* Dashboard principal */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Score circular */}
              <div className="bg-white p-6 rounded-xl shadow-sm border">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-blue-600" />
                  Evaluación General
                </h3>
                <div className="text-center">
                  <CircularProgress
                    percentage={candidate.cv_info?.overall_score || 0}
                    color={getScoreColor(candidate.cv_info?.overall_score || 0)}
                  />
                  <p className="mt-4 text-sm text-gray-600">
                    {getScoreLabel(candidate.cv_info?.overall_score || 0)}{" "}
                    candidato para la posición
                  </p>
                </div>
              </div>

              {/* Información profesional */}
              <div className="bg-white p-6 rounded-xl shadow-sm border">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Briefcase className="w-5 h-5 text-green-600" />
                  Perfil Profesional
                </h3>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Industria:</span>
                    <span className="font-medium">
                      {candidate.professional_info?.industria ||
                        "No especificada"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Rol:</span>
                    <span className="font-medium">
                      {candidate.professional_info?.rol || "No especificado"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Seniority:</span>
                    <span className="font-medium">
                      {candidate.professional_info?.puesto ||
                        metrics.experienceLevel}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Experiencia:</span>
                    <span className="font-medium text-blue-600">
                      {candidate.professional_info?.anhos_experiencia || 0} años
                    </span>
                  </div>
                </div>
              </div>

              {/* Completitud del perfil */}
              <div className="bg-white p-6 rounded-xl shadow-sm border">
                <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                  <Target className="w-5 h-5 text-purple-600" />
                  Completitud del Perfil
                </h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">
                      Información Personal
                    </span>
                    <span className="text-sm font-medium text-green-600">
                      {candidate.personal_info?.nombre &&
                      candidate.personal_info?.email
                        ? "100%"
                        : "Parcial"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">
                      Datos Profesionales
                    </span>
                    <span className="text-sm font-medium text-green-600">
                      {candidate.professional_info?.industria
                        ? "100%"
                        : "Parcial"}
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Habilidades</span>
                    <span className="text-sm font-medium text-blue-600">
                      {metrics.skillCount} detectadas
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">Idiomas</span>
                    <span className="text-sm font-medium text-blue-600">
                      {metrics.languageCount} idiomas
                    </span>
                  </div>

                  {/* Barra de progreso general */}
                  <div className="pt-2">
                    <div className="flex justify-between mb-2">
                      <span className="text-sm font-medium text-gray-700">
                        Perfil Completo
                      </span>
                      <span className="text-sm text-gray-500">
                        {metrics.profileCompleteness}%
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-gradient-to-r from-blue-500 to-purple-500 h-2 rounded-full transition-all duration-1000"
                        style={{ width: `${metrics.profileCompleteness}%` }}
                      ></div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Skills Tab */}
        {activeTab === "skills" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-xl shadow-sm border">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Award className="w-5 h-5 text-blue-600" />
                Habilidades Técnicas
              </h3>
              {skillsWithLevels.length > 0 ? (
                <div className="space-y-4">
                  {skillsWithLevels.map((skill, index) => (
                    <SkillBar
                      key={index}
                      skill={skill.name}
                      level={skill.level}
                      color={
                        index % 3 === 0
                          ? "bg-blue-500"
                          : index % 3 === 1
                          ? "bg-green-500"
                          : "bg-purple-500"
                      }
                    />
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">
                  No se detectaron habilidades específicas en el CV
                </p>
              )}
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Languages className="w-5 h-5 text-green-600" />
                Idiomas
              </h3>
              {candidate.skills_and_languages?.idiomas?.length > 0 ? (
                <div className="flex flex-wrap gap-3">
                  {candidate.skills_and_languages.idiomas.map(
                    (language, index) => (
                      <span
                        key={index}
                        className="px-4 py-2 bg-green-100 text-green-800 rounded-full text-sm font-medium"
                      >
                        {language}
                      </span>
                    )
                  )}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">
                  No se detectaron idiomas específicos
                </p>
              )}

              <div className="mt-6 pt-6 border-t">
                <h4 className="font-semibold mb-3">Análisis de Competencias</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div className="text-center p-3 bg-blue-50 rounded-lg">
                    <div className="font-semibold text-blue-600">
                      {metrics.skillCount + metrics.languageCount}
                    </div>
                    <div className="text-gray-600">Competencias Totales</div>
                  </div>
                  <div className="text-center p-3 bg-green-50 rounded-lg">
                    <div className="font-semibold text-green-600">
                      {metrics.experienceLevel}
                    </div>
                    <div className="text-gray-600">Nivel de Seniority</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Experience Tab */}
        {activeTab === "experience" && (
          <div className="bg-white p-6 rounded-xl shadow-sm border">
            <h3 className="text-lg font-semibold mb-6 flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-blue-600" />
              Experiencia Profesional
            </h3>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="p-4 border border-gray-200 rounded-lg">
                <h4 className="font-semibold text-gray-700 mb-2">
                  Años de Experiencia
                </h4>
                <p className="text-3xl font-bold text-blue-600 mb-1">
                  {candidate.professional_info?.anhos_experiencia || 0}
                </p>
                <p className="text-sm text-gray-500">años</p>
              </div>

              <div className="p-4 border border-gray-200 rounded-lg">
                <h4 className="font-semibold text-gray-700 mb-2">
                  Industria Principal
                </h4>
                <p className="text-lg font-medium text-gray-800">
                  {candidate.professional_info?.industria || "No especificada"}
                </p>
              </div>

              <div className="p-4 border border-gray-200 rounded-lg">
                <h4 className="font-semibold text-gray-700 mb-2">
                  Rol Actual/Último
                </h4>
                <p className="text-lg font-medium text-gray-800">
                  {candidate.professional_info?.rol || "No especificado"}
                </p>
              </div>
            </div>

            <div className="mt-8">
              <h4 className="font-semibold mb-4">Análisis de Experiencia</h4>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-sm text-gray-600 mb-2">
                  <strong>Nivel de Seniority:</strong> {metrics.experienceLevel}
                </p>
                <p className="text-sm text-gray-600 mb-2">
                  <strong>Perfil Profesional:</strong>{" "}
                  {candidate.professional_info?.anhos_experiencia >= 5
                    ? "Profesional experimentado con sólida trayectoria"
                    : candidate.professional_info?.anhos_experiencia >= 2
                    ? "Profesional con experiencia media, en crecimiento"
                    : "Profesional junior o en inicio de carrera"}
                </p>
                <p className="text-sm text-gray-600">
                  <strong>Valor de Mercado:</strong> {metrics.marketValue} según
                  el análisis del CV
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Contact Tab */}
        {activeTab === "contact" && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="bg-white p-6 rounded-xl shadow-sm border">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <User className="w-5 h-5 text-blue-600" />
                Información de Contacto
              </h3>

              <div className="space-y-4">
                <div className="flex items-center gap-3">
                  <Mail className="w-5 h-5 text-gray-400" />
                  <div>
                    <p className="text-sm text-gray-600">Email</p>
                    <p className="font-medium">
                      {candidate.personal_info?.email ||
                        candidate.classic_data?.email ||
                        "No disponible"}
                    </p>
                  </div>
                </div>

                {(candidate.personal_info?.telefono ||
                  candidate.classic_data?.telefono) && (
                  <div className="flex items-center gap-3">
                    <Phone className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-600">Teléfono</p>
                      <p className="font-medium">
                        {candidate.personal_info?.telefono ||
                          candidate.classic_data?.telefono}
                      </p>
                    </div>
                  </div>
                )}

                {candidate.personal_info?.ubicacion && (
                  <div className="flex items-center gap-3">
                    <MapPin className="w-5 h-5 text-gray-400" />
                    <div>
                      <p className="text-sm text-gray-600">Ubicación</p>
                      <p className="font-medium">
                        {candidate.personal_info.ubicacion}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            </div>

            <div className="bg-white p-6 rounded-xl shadow-sm border">
              <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
                <Globe className="w-5 h-5 text-green-600" />
                Enlaces Profesionales
              </h3>

              <div className="space-y-3">
                {candidate.personal_info?.linkedin && (
                  <a
                    href={candidate.personal_info.linkedin}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-3 p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition"
                  >
                    <Linkedin className="w-5 h-5 text-blue-600" />
                    <div>
                      <p className="font-medium text-blue-800">LinkedIn</p>
                      <p className="text-sm text-blue-600">
                        Ver perfil profesional
                      </p>
                    </div>
                  </a>
                )}

                {candidate.personal_info?.github && (
                  <a
                    href={candidate.personal_info.github}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition"
                  >
                    <Github className="w-5 h-5 text-gray-700" />
                    <div>
                      <p className="font-medium text-gray-800">GitHub</p>
                      <p className="text-sm text-gray-600">
                        Repositorio de código
                      </p>
                    </div>
                  </a>
                )}

                {candidate.personal_info?.portafolio && (
                  <a
                    href={candidate.personal_info.portafolio}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-3 p-3 bg-purple-50 rounded-lg hover:bg-purple-100 transition"
                  >
                    <Globe className="w-5 h-5 text-purple-600" />
                    <div>
                      <p className="font-medium text-purple-800">Portafolio</p>
                      <p className="text-sm text-purple-600">Ver trabajos</p>
                    </div>
                  </a>
                )}

                {!candidate.personal_info?.linkedin &&
                  !candidate.personal_info?.github &&
                  !candidate.personal_info?.portafolio && (
                    <div className="text-center py-8 text-gray-500">
                      <Globe className="w-8 h-8 mx-auto mb-2 text-gray-300" />
                      <p>No hay enlaces profesionales disponibles</p>
                    </div>
                  )}
              </div>

              {/* Información adicional del CV */}
              <div className="mt-6 pt-6 border-t">
                <h4 className="font-semibold mb-3 flex items-center gap-2">
                  <Activity className="w-4 h-4 text-gray-600" />
                  Estado del CV
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-600">ID del CV:</span>
                    <span className="font-mono text-xs bg-gray-100 px-2 py-1 rounded">
                      {candidate.cv_info?.id || candidateId}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Archivo:</span>
                    <span className="text-xs">
                      {candidate.cv_info?.filename || "No disponible"}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Estado:</span>
                    <span
                      className={`text-xs px-2 py-1 rounded-full ${
                        candidate.cv_info?.processed_status === "completed"
                          ? "bg-green-100 text-green-800"
                          : "bg-yellow-100 text-yellow-800"
                      }`}
                    >
                      {candidate.cv_info?.processed_status === "completed"
                        ? "Procesado"
                        : "En proceso"}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Floating Action Buttons */}
      <div className="fixed bottom-6 right-6 space-y-3">
        <button className="flex items-center justify-center w-12 h-12 bg-blue-600 text-white rounded-full shadow-lg hover:bg-blue-700 transition-all hover:scale-110">
          <Download className="w-5 h-5" />
        </button>
        <button className="flex items-center justify-center w-12 h-12 bg-green-600 text-white rounded-full shadow-lg hover:bg-green-700 transition-all hover:scale-110">
          <MessageCircle className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
}
