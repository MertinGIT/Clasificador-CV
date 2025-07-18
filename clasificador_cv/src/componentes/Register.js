import React, { useState, useRef, useEffect } from 'react';
import './UserChat.css';
import axios from 'axios';

// URL base para la API
const API_URL = 'http://localhost:8000';

function Register({ username, onLogout }) {
  const [message, setMessage] = useState('');
  const [conversations, setConversations] = useState([]);
  const [activeConversation, setActiveConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [sidebarVisible, setSidebarVisible] = useState(true);
  const userMenuRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Cerrar el menú de usuario al hacer clic fuera de él
  useEffect(() => {
    function handleClickOutside(event) {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target)) {
        setShowUserMenu(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [userMenuRef]);

  // Cargar conversaciones al inicio
  useEffect(() => {
    fetchConversations();
  }, []);

  // Cargar mensajes cuando se selecciona una conversación
  useEffect(() => {
    if (activeConversation) {
      fetchMessages(activeConversation);
    } else {
      setMessages([]);
    }
  }, [activeConversation]);

  // Scroll al fondo de los mensajes cuando se añade uno nuevo
  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Obtener todas las conversaciones
  const fetchConversations = async () => {
    try {
      const response = await axios.get(`${API_URL}/conversations`);
      setConversations(response.data);
      
      // Si hay conversaciones pero ninguna activa, seleccionar la primera
      if (response.data.length > 0 && !activeConversation) {
        setActiveConversation(response.data[0].id);
      }
    } catch (error) {
      console.error('Error al cargar conversaciones:', error);
    }
  };

  // Obtener mensajes de una conversación específica
  const fetchMessages = async (conversationId) => {
    try {
      const response = await axios.get(`${API_URL}/conversations/${conversationId}`);
      setMessages(response.data.messages);
    } catch (error) {
      console.error('Error al cargar mensajes:', error);
    }
  };

  // Enviar un mensaje
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (message.trim()) {
      // Crear un mensaje temporal para mostrar inmediatamente
      const tempUserMessage = {
        id: `temp-${Date.now()}`,
        text: message,
        sender: 'user',
        timestamp: new Date().toISOString()
      };
      
      // Añadir el mensaje del usuario a la interfaz inmediatamente
      setMessages(prev => [...prev, tempUserMessage]);
      
      // Guardar el mensaje para enviarlo a la API
      const messageText = message;
      
      // Limpiar el campo de entrada
      setMessage('');
      
      // Indicar que se está procesando
      setIsLoading(true);
      
      try {
        // Preparar la petición
        const messageData = {
          text: messageText,
          conversation_id: activeConversation
        };
        
        // Enviar el mensaje y obtener respuesta
        const response = await axios.post(`${API_URL}/messages`, messageData);
        
        // Si es una nueva conversación, actualizamos la lista
        if (!activeConversation) {
          await fetchConversations();
          // La API debería devolver la ID de la conversación creada
          const newConversationId = response.data.conversation_id;
          setActiveConversation(newConversationId);
        } else {
          // Actualizar los mensajes de la conversación actual con los del servidor
          await fetchMessages(activeConversation);
        }
      } catch (error) {
        console.error('Error al enviar mensaje:', error);
        // Notificar al usuario del error
        alert('No se pudo enviar el mensaje. Por favor intenta de nuevo.');
      } finally {
        setIsLoading(false);
      }
    }
  };

  // Toggle para mostrar/ocultar la barra lateral
  const toggleSidebar = () => {
    setSidebarVisible(!sidebarVisible);
  };

  // Función para verificar si una fecha es hoy
  const isToday = (dateStr) => {
    const date = new Date(dateStr);
    const today = new Date();
    return date.getDate() === today.getDate() &&
      date.getMonth() === today.getMonth() &&
      date.getFullYear() === today.getFullYear();
  };

  // Función para verificar si una fecha es ayer
  const isYesterday = (dateStr) => {
    const date = new Date(dateStr);
    const yesterday = new Date();
    yesterday.setDate(yesterday.getDate() - 1);
    return date.getDate() === yesterday.getDate() &&
      date.getMonth() === yesterday.getMonth() &&
      date.getFullYear() === yesterday.getFullYear();
  };

  // Función para verificar si una fecha está dentro de los últimos 7 días (excluyendo hoy y ayer)
  const isLast7Days = (dateStr) => {
    const date = new Date(dateStr);
    const today = new Date();
    const sevenDaysAgo = new Date();
    sevenDaysAgo.setDate(today.getDate() - 7);
    return date > sevenDaysAgo && !isToday(dateStr) && !isYesterday(dateStr);
  };

  // Función para verificar si una fecha está dentro de los últimos 30 días (excluyendo los últimos 7)
  const isLast30Days = (dateStr) => {
    const date = new Date(dateStr);
    const today = new Date();
    const thirtyDaysAgo = new Date();
    const sevenDaysAgo = new Date();
    thirtyDaysAgo.setDate(today.getDate() - 30);
    sevenDaysAgo.setDate(today.getDate() - 7);
    return date > thirtyDaysAgo && date <= sevenDaysAgo;
  };

  // Agrupar conversaciones por fecha
  const groupConversationsByDate = () => {
    // Filtramos las conversaciones por el término de búsqueda primero
    const filtered = conversations.filter(conv => 
      conv.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      conv.preview.toLowerCase().includes(searchTerm.toLowerCase())
    );
    
    // Organizamos las conversaciones por categoría de tiempo
    const groups = {
      today: filtered.filter(conv => isToday(conv.timestamp)),
      yesterday: filtered.filter(conv => isYesterday(conv.timestamp)),
      last7Days: filtered.filter(conv => isLast7Days(conv.timestamp)),
      last30Days: filtered.filter(conv => isLast30Days(conv.timestamp)),
      older: filtered.filter(conv => {
        const date = new Date(conv.timestamp);
        const thirtyDaysAgo = new Date();
        thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);
        return date <= thirtyDaysAgo;
      })
    };
    
    // Organizar las conversaciones más antiguas por mes
    const olderByMonth = {};
    groups.older.forEach(conv => {
      const date = new Date(conv.timestamp);
      const monthYear = `${date.getMonth() + 1}/${date.getFullYear()}`;
      if (!olderByMonth[monthYear]) {
        olderByMonth[monthYear] = [];
      }
      olderByMonth[monthYear].push(conv);
    });
    
    return { ...groups, olderByMonth };
  };

  const groupedConversations = groupConversationsByDate();

  // Obtener el nombre del mes en español
  const getMonthName = (monthNumber) => {
    const monthNames = [
      'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
      'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
    ];
    return monthNames[monthNumber - 1];
  };

  // Crear nueva conversación
  const handleNewConversation = () => {
    setActiveConversation(null);
    setMessages([]);
  };

  // Guardar conversación en el almacenamiento local
  const saveToLocalStorage = () => {
    if (messages.length > 0) {
      // Crear un objeto con los datos de la conversación actual
      const conversationData = {
        id: activeConversation || `local-${Date.now()}`,
        messages: messages,
        timestamp: new Date().toISOString()
      };
      
      // Obtener conversaciones existentes del localStorage
      const storedConversations = JSON.parse(localStorage.getItem('chatConversations') || '[]');
      
      // Verificar si esta conversación ya existe
      const existingIndex = storedConversations.findIndex(c => c.id === conversationData.id);
      
      if (existingIndex >= 0) {
        // Actualizar la conversación existente
        storedConversations[existingIndex] = conversationData;
      } else {
        // Añadir nueva conversación
        storedConversations.push(conversationData);
      }
      
      // Guardar en localStorage
      localStorage.setItem('chatConversations', JSON.stringify(storedConversations));
    }
  };

  // Cargar conversaciones del almacenamiento local cuando falla la API
  const loadFromLocalStorage = () => {
    const storedConversations = JSON.parse(localStorage.getItem('chatConversations') || '[]');
    if (storedConversations.length > 0) {
      return storedConversations;
    }
    return [];
  };

  // Guardar en localStorage cuando hay cambios en los mensajes
  useEffect(() => {
    if (messages.length > 0) {
      saveToLocalStorage();
    }
  }, [messages]);

  return (
    <div className={`user-container ${sidebarVisible ? '' : 'sidebar-hidden'}`}>
      {/* Botón toggle para mostrar/ocultar sidebar */}
      <button className="toggle-sidebar-button" onClick={toggleSidebar}>
        {sidebarVisible ? '←' : '→'}
      </button>
      
      {/* Sidebar con las conversaciones */}
      <div className={`user-sidebar ${sidebarVisible ? 'visible' : 'hidden'}`}>
        <div className="sidebar-header">
          {/* Quitamos el avatar de aquí */}
        </div>
        
        <div className="search-container">
          <input
            type="text"
            placeholder="Buscar conversación..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          <button 
            className="new-chat-button"
            onClick={handleNewConversation}
          >
            Nueva conversación
          </button>
        </div>
        <div className="conversations-list">
          {/* Sección de Hoy */}
          {groupedConversations.today.length > 0 && (
            <>
              <div className="date-header">Hoy</div>
              {groupedConversations.today.map(conv => (
                <div 
                  key={conv.id} 
                  className={`conversation-item ${activeConversation === conv.id ? 'active' : ''}`}
                  onClick={() => setActiveConversation(conv.id)}
                >
                  <h3>{conv.title}</h3>
                  <p>{conv.preview}</p>
                </div>
              ))}
            </>
          )}
          
          {/* Sección de Ayer */}
          {groupedConversations.yesterday.length > 0 && (
            <>
              <div className="date-header">Ayer</div>
              {groupedConversations.yesterday.map(conv => (
                <div 
                  key={conv.id} 
                  className={`conversation-item ${activeConversation === conv.id ? 'active' : ''}`}
                  onClick={() => setActiveConversation(conv.id)}
                >
                  <h3>{conv.title}</h3>
                  <p>{conv.preview}</p>
                </div>
              ))}
            </>
          )}
          
          {/* Sección de 7 días anteriores */}
          {groupedConversations.last7Days.length > 0 && (
            <>
              <div className="date-header">7 días anteriores</div>
              {groupedConversations.last7Days.map(conv => (
                <div 
                  key={conv.id} 
                  className={`conversation-item ${activeConversation === conv.id ? 'active' : ''}`}
                  onClick={() => setActiveConversation(conv.id)}
                >
                  <h3>{conv.title}</h3>
                  <p>{conv.preview}</p>
                </div>
              ))}
            </>
          )}
          
          {/* Sección de 30 días anteriores */}
          {groupedConversations.last30Days.length > 0 && (
            <>
              <div className="date-header">30 días anteriores</div>
              {groupedConversations.last30Days.map(conv => (
                <div 
                  key={conv.id} 
                  className={`conversation-item ${activeConversation === conv.id ? 'active' : ''}`}
                  onClick={() => setActiveConversation(conv.id)}
                >
                  <h3>{conv.title}</h3>
                  <p>{conv.preview}</p>
                </div>
              ))}
            </>
          )}
          
          {/* Secciones por mes para conversaciones más antiguas */}
          {Object.keys(groupedConversations.olderByMonth).map(monthYear => {
            const [month, year] = monthYear.split('/');
            return (
              <React.Fragment key={monthYear}>
                <div className="date-header">{getMonthName(parseInt(month))} {year}</div>
                {groupedConversations.olderByMonth[monthYear].map(conv => (
                  <div 
                    key={conv.id} 
                    className={`conversation-item ${activeConversation === conv.id ? 'active' : ''}`}
                    onClick={() => setActiveConversation(conv.id)}
                  >
                    <h3>{conv.title}</h3>
                    <p>{conv.preview}</p>
                  </div>
                ))}
              </React.Fragment>
            );
          })}
        </div>
      </div>
      <div className="chat-area">
        {/* Avatar de usuario en la esquina superior derecha del chat */}
        <div className="chat-header">
          <div className="user-profile" ref={userMenuRef}>
            <div 
              className="user-avatar" 
              onClick={() => setShowUserMenu(!showUserMenu)}
            >
              {username.charAt(0).toUpperCase()}
            </div>
            {showUserMenu && (
              <div className="user-menu">
                <div className="menu-item">Configuraciones</div>
                <div className="menu-item" onClick={onLogout}>Cerrar sesión</div>
              </div>
            )}
          </div>
        </div>
        
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="empty-chat-message">
              <p>No hay mensajes. Inicia una nueva conversación.</p>
            </div>
          ) : (
            messages.map(msg => (
              <div key={msg.id} className={`message ${msg.sender}`}>
                {msg.text}
                <span className="message-time">
                  {msg.id.includes('temp-') ? 'Enviando...' : 
                    new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                </span>
              </div>
            ))
          )}
          <div ref={messagesEndRef} />
          {isLoading && (
            <div className="message bot loading">
              <div className="typing-indicator">
                <span></span>
                <span></span>
                <span></span>
              </div>
            </div>
          )}
        </div>
        <form className="message-input-container" onSubmit={handleSendMessage}>
          <input
            type="text"
            placeholder="Escribe un mensaje..."
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            className="message-input"
            disabled={isLoading}
            autoFocus
          />
          <button type="submit" className="send-button" disabled={isLoading || !message.trim()}>
            <span>➤</span>
          </button>
        </form>
      </div>
    </div>
  );
}

export default Register;