import { Link } from "react-router-dom";

function login() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-[#494949] font-sans text-sm">
      <div className="w-[65vh] h-[65vh] border border-[#e0e0e0] flex flex-col justify-center items-center bg-white rounded-md shadow-md">
        {/* Logo y título */}
        <div className="p-5 text-center">
          <img
            src="https://cdn-icons-png.flaticon.com/256/3305/3305969.png"
            alt="Logo"
            className="w-20 h-20 mb-2"
          />
          <h2 className="text-2xl font-bold m-0 p-0 logo-title">Inovo</h2>
        </div>

        <form className="flex flex-col w-full items-center">
          <input
            type="text"
            placeholder="Usuario"
            className="w-[359px] mb-[15px] p-[10px] border border-[#e0e0e0] rounded"
          />
          <input
            type="password"
            placeholder="Contraseña"
            className="w-[359px] mb-[15px] p-[10px] border border-[#e0e0e0] rounded"
          />

          <div className="flex justify-evenly w-full mt-5 px-6">
            <button
              type="submit"
              className="rounded-full border-none bg-black text-white text-base px-6 py-2 transition duration-1000 hover:bg-gray-300 hover:text-black"
            >
              Iniciar Sesión
            </button>

            <Link
              to="/register"
              className="no-underline text-black text-[25px] transition duration-1000 hover:text-gray-500"
            >
              Registrarse
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
}
export default login;
