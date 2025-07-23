import React, { useState } from "react";

function UploadCV() {
  const [file, setFile] = useState(null);
  const [message, setMessage] = useState("");

  const handleFileChange = (e) => {
    setFile(e.target.files[0]);
    setMessage("");
  };

  const handleUpload = () => {
    if (!file) {
      setMessage("Por favor, selecciona un archivo.");
      return;
    }

    // Aquí iría la lógica para enviar el archivo al backend
    setMessage(`Archivo "${file.name}" subido correctamente.`);
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 px-4">
      <div className="bg-white dark:bg-gray-900 p-8 rounded-2xl shadow-lg w-full max-w-md">
        <h2 className="text-3xl font-bold text-center text-gray-800 dark:text-white mb-6">
          Subir CV
        </h2>

        <div className="mb-4">
          <label
            htmlFor="cv-upload"
            className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2"
          >
            Selecciona tu CV (PDF, DOC, DOCX)
          </label>
          <input
            id="cv-upload"
            type="file"
            accept=".pdf,.doc,.docx"
            onChange={handleFileChange}
            className="block w-full text-sm text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg cursor-pointer focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {message && (
          <p className="text-sm text-center mb-4 text-red-600 dark:text-red-400">
            {message}
          </p>
        )}

        <button
          onClick={handleUpload}
          className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold rounded-lg transition duration-200"
        >
          Subir
        </button>
      </div>
    </div>
  );
}

export default UploadCV;
