import React from "react";
import "./Login.css"; // reutilizamos el CSS existente

function Register() {
  return (
    <div className="flex justify-center items-center h-screen">
      <div className="login-container bg-white rounded-md flex flex-col items-center shadow-lg p-6">
        {/* Logo y título */}
        <div className="login-logo flex flex-col items-center">
          <img
            src="https://sdmntpreastus.oaiusercontent.com/files/00000000-0108-61f9-99bd-460ef6ea0ce9/raw?se=2025-07-23T05%3A03%3A13Z&sp=r&sv=2024-08-04&sr=b&scid=d2f806c9-441d-5ce0-be2e-be93f718571e&skoid=02b7f7b5-29f8-416a-aeb6-99464748559d&sktid=a48cca56-e6da-484e-a814-9c849652bcb3&skt=2025-07-22T23%3A52%3A34Z&ske=2025-07-23T23%3A52%3A34Z&sks=b&skv=2024-08-04&sig=oGV3mcDaxdkIdvu8qCcFZeH1Z8MTG4nqA1vP1fHjaIA%3D"
            alt="Logo"
            className="w-20 h-20 mb-2"
          />
          <h2 className="logo-title text-2xl font-bold text-center">
            Crear Cuenta
          </h2>
        </div>

        {/* Formulario */}
        <form className="inputs-form mt-6">
          <input type="text" placeholder="Nombre completo" />
          <input type="email" placeholder="Correo electrónico" />
          <input type="text" placeholder="Nombre de usuario" />
          <input type="password" placeholder="Contraseña" />
          <input type="password" placeholder="Confirmar contraseña" />

          <div className="flex justify-evenly w-full mt-5 px-6">
            <button type="submit" className="login-button px-6 py-2">
              Registrarme
            </button>
            <a
              href="/"
              className="no-underline text-black text-[20px] transition duration-1000 hover:text-gray-900"
            >
              Ya tengo cuenta
            </a>
          </div>
        </form>
      </div>
    </div>
  );
}

export default Register;
