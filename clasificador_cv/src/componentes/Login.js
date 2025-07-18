import { Link } from 'react-router-dom';

function login(){

return(

    <div className="login-container">
        <div className="login-logo">
            <img src='' className="login-img"/>
        </div>
    <form>   
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