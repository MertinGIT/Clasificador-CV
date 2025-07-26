import React, { useState, useRef } from "react";
import axios from "axios";

function UploadDoc() {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState({});
  const [message, setMessage] = useState({ text: "", type: "" });
  const fileInputRef = useRef(null);

  const fileTypes = {
    pdf: "PDF",
    docx: "Word",
    xlsx: "Excel",
    xls: "Excel",
    csv: "CSV",
    txt: "Texto",
  };

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    setFiles(selectedFiles);
  };

  const removeFile = (index) => {
    const updatedFiles = [...files];
    updatedFiles.splice(index, 1);
    setFiles(updatedFiles);
  };

  const simulateUpload = async (fileName) => {
    return new Promise((resolve) => {
      let progress = 0;
      const interval = setInterval(() => {
        progress += Math.floor(Math.random() * 10) + 5;
        if (progress > 100) progress = 100;

        setUploadProgress((prev) => ({
          ...prev,
          [fileName]: progress,
        }));

        if (progress === 100) {
          clearInterval(interval);
          resolve();
        }
      }, 300);
    });
  };

  const uploadFiles = async () => {
    if (files.length === 0) {
      setMessage({
        text: "Por favor selecciona al menos un archivo",
        type: "error",
      });
      return;
    }

    setUploading(true);
    setMessage({ text: "", type: "" });

    const initialProgress = {};
    files.forEach((file) => {
      initialProgress[file.name] = 0;
    });
    setUploadProgress(initialProgress);

    for (const file of files) {
      try {
        const uploadAnimation = simulateUpload(file.name);

        const formData = new FormData();
        formData.append("file", file);

        const response = await axios.post(
          "http://localhost:8000/documents/upload",
          formData,
          {
            headers: {
              "Content-Type": "multipart/form-data",
            },
          }
        );

        await uploadAnimation;
        console.log(`Archivo ${file.name} subido exitosamente:`, response.data);
      } catch (error) {
        console.error(`Error al subir ${file.name}:`, error);
        setMessage({
          text: `Error al subir ${file.name}: ${
            error.response?.data?.detail || error.message
          }`,
          type: "error",
        });
      }
    }

    setMessage({
      text: "Todos los archivos han sido procesados",
      type: "success",
    });
    setUploading(false);
    setFiles([]);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const getFileType = (fileName) => {
    const extension = fileName.split(".").pop().toLowerCase();
    return fileTypes[extension] || "Desconocido";
  };

  const formatFileSize = (size) => {
    if (size < 1024) return size + " B";
    else if (size < 1024 * 1024) return (size / 1024).toFixed(2) + " KB";
    else return (size / (1024 * 1024)).toFixed(2) + " MB";
  };

  return (
    <div className="min-h-screen bg-gray-100 py-10 px-4">
      <div className="max-w-3xl mx-auto bg-white shadow-lg rounded-xl p-8">
        <h2 className="text-2xl font-bold mb-6 text-gray-800">
          Subida de Documentos
        </h2>

        {/* Área de carga */}
        <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center mb-6 bg-gray-50">
          <div className="text-4xl mb-2">📄</div>
          <p className="mb-2 text-gray-600">
            Arrastra y suelta archivos aquí o
          </p>

          <input
            type="file"
            id="file-upload"
            multiple
            onChange={handleFileChange}
            ref={fileInputRef}
            accept=".pdf,.docx,.xlsx,.xls,.csv,.txt"
            className="hidden"
          />
          <label
            htmlFor="file-upload"
            className="cursor-pointer inline-block bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded shadow"
          >
            Seleccionar archivos
          </label>
          <p className="text-sm text-gray-500 mt-2">
            Formatos soportados: PDF, DOCX, XLSX, XLS, CSV, TXT
          </p>
        </div>

        {/* Lista de archivos */}
        {files.length > 0 && (
          <div className="mb-6">
            <h3 className="text-lg font-semibold mb-4 text-gray-700">
              Archivos seleccionados ({files.length})
            </h3>

            <div className="space-y-4">
              {files.map((file, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between bg-gray-100 rounded-lg p-4 shadow"
                >
                  <div>
                    <div className="text-sm font-bold">
                      {getFileType(file.name)}
                    </div>
                    <div className="text-gray-700">{file.name}</div>
                    <div className="text-xs text-gray-500">
                      {formatFileSize(file.size)}
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    {uploading ? (
                      <div className="w-40 relative">
                        <div className="h-2 bg-blue-200 rounded">
                          <div
                            className="h-2 bg-blue-600 rounded transition-all"
                            style={{
                              width: `${uploadProgress[file.name] || 0}%`,
                            }}
                          />
                        </div>
                        <div className="text-xs text-right mt-1 text-gray-600">
                          {uploadProgress[file.name] || 0}%
                        </div>
                      </div>
                    ) : (
                      <button
                        onClick={() => removeFile(index)}
                        className="text-red-600 hover:text-red-800 text-sm"
                      >
                        Eliminar
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Mensaje */}
            {message.text && (
              <div
                className={`mt-4 p-3 rounded ${
                  message.type === "success"
                    ? "bg-green-100 text-green-700"
                    : "bg-red-100 text-red-700"
                }`}
              >
                {message.text}
              </div>
            )}

            {/* Botón de subida */}
            <div className="mt-6 text-right">
              <button
                onClick={uploadFiles}
                disabled={uploading}
                className={`px-6 py-2 rounded shadow text-white ${
                  uploading ? "bg-gray-400" : "bg-green-600 hover:bg-green-700"
                }`}
              >
                {uploading ? "Subiendo..." : "Subir archivos"}
              </button>
            </div>
          </div>
        )}

        {/* Info adicional */}
        <div className="mt-8 text-gray-700">
          <h3 className="font-semibold mb-2">Documentos para sistema RAG</h3>
          <ul className="list-disc list-inside text-sm space-y-1">
            <li>Los archivos serán convertidos a texto</li>
            <li>Se dividirán en fragmentos para su procesamiento</li>
            <li>Se generarán embeddings para búsqueda vectorial</li>
            <li>Serán accesibles para consultas a través del chat</li>
          </ul>
        </div>
      </div>
    </div>
  );
}

export default UploadDoc;
