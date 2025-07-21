import { Link } from 'react-router-dom';
import './Login.css'
function login(){

return(

    <div className="login-container">
        <div className="login-logo">
            <img src='https://multisolutionspy.com/images/logo_icono.png' className="login-img"/>
            <h1 className='logo-title'>Nombre Empresa</h1>
        </div>
    <form className='inputs-form'>   
        <input 
        type="text"
        placeholder="Usuario"        
        />
        <input 
        type="password"
        placeholder="Contraseña"
        />
    </form>
        <div className="buttons-container">
            <button type="submit" className="login-button">Iniciar Sesion</button>
            <Link to="/register" className="register-button">Registrarse</Link>
        </div>
    </div>



);




}

export default login;