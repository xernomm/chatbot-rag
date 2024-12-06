import React, { useEffect, useState } from 'react';
import axios from 'axios';
import '../style/Chatbox.css'
import '../style/ChatField.css'
import prima from '../img/primalogo.png'
import { FaUserCircle } from "react-icons/fa";
import '../style/Font.css'

const Chats = () => {
  const [chats, setChats] = useState([]);
  const [error, setError] = useState('');
  const host = process.env.REACT_APP_API_HOST                   
  const port = process.env.REACT_APP_API_PORT 

  // Fetch chats from the backend
  useEffect(() => {
    const fetchChats = async () => {
      try {
        const response = await axios.get(`${host}:${port}/chat-history`);
        console.log(response.data.chat_history)
        setChats(response.data.chat_history || []);
      } catch (err) {
        setError('Failed to fetch chat history');
        console.error(err);
      }
    };

    // Fetch chats initially
    fetchChats();

    // Set interval to fetch chats every 1 second
    const intervalId = setInterval(fetchChats, 1000);

    // Cleanup function to clear the interval on component unmount
    return () => clearInterval(intervalId);
  }, [host, port]);

  return (
    <div>
      <h1 className='text-light display-6 text-center fw-bold titleApp'>Vanka-AI 2.0</h1>
      {error && <p style={{ color: 'red' }}>{error}</p>}
      <div className='chatfield'>
        {chats.length > 0 ? (
          chats.map((chat, index) => (
            <div key={index}>
              <div className={chat.role === 'user' ? 'd-flex col-12 justify-content-end' : 'd-flex col-12 justify-content-start'}>
                {chat.role === 'bot' && (
                  <div className='d-flex mt-2'>
                    <img style={{
                      width: '40px',
                      height: '40px',
                      marginRight: '5px'
                    }} src={prima} alt="" />
                  </div>
                )}
                <div className={chat.role === 'user' ? 'user-message' : 'bot-message'}>
                  {chat.message}
                </div>
                {chat.role === 'user' && (
                  <div className='d-flex align-items-center'>
                    <FaUserCircle className='text-white ms-2 px32' />
                  </div>
                )}
              </div>
              <div>
                <small className={`text-light px12 ${chat.role === 'user' ? 'd-flex col-12 justify-content-end' : 'd-flex col-12 justify-content-start'}`}>
                  {new Date(chat.timestamp).toLocaleString('id-ID', {
                    year: 'numeric',
                    month: 'short',
                    day: 'numeric',
                    hour: 'numeric',
                    minute: 'numeric',
                    hour12: false,
                  })}
                </small>
              </div>
            </div>
          ))
        ) : (
          <p>No chats available.</p>
        )}
      </div>
    </div>
  );
};

export default Chats;