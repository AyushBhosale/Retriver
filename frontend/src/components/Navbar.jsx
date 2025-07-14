import React, { useState, useEffect } from 'react';
import { apiClient } from '../utils/api';
import { Menu, X, Trash2 } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

const Navbar = () => {
  const [chatTitles, setChatTitles] = useState([]);
  const [isOpen, setIsOpen] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchChats();
  }, []);

  const fetchChats = () => {
    apiClient
      .get('/rag/getConversations', {
        headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
      })
      .then((response) => setChatTitles(response.data.data))
      .catch(console.error);
  };

  const handleNewClick = () => {
    navigate('/');
  };

  const handleDelete = async (id, title) => {
    const confirmDelete = window.confirm(`Delete conversation "${title}"?`);
    if (!confirmDelete) return;

    try {
      await apiClient.delete('/rag/deleteConversation', {
        params: { conId: id },
        headers: {
          Authorization: `Bearer ${localStorage.getItem('token')}`,
        },
      });

      // Filter out deleted conversation from state
      setChatTitles((prev) => prev.filter((chat) => chat.id !== id));
    } catch (err) {
      console.error('Delete failed:', err);
      alert('Failed to delete conversation');
    }
  };

  return (
    <div className="flex flex-col h-full w-64 bg-[#7e22ce] text-white shadow-md p-4 flex-shrink-0">
      {/* Mobile toggle button */}
      <div className="md:hidden flex justify-between items-center mb-2">
        <h1 className="text-lg font-semibold">Chats</h1>
        <button onClick={() => setIsOpen(!isOpen)}>
          {isOpen ? <X size={22} /> : <Menu size={22} />}
        </button>
      </div>

      {/* Sidebar content */}
      <div className={`${isOpen ? 'block' : 'hidden'} md:block overflow-hidden`}>
        <button
          onClick={handleNewClick}
          className="w-full bg-white text-[#7e22ce] font-semibold py-2 rounded-lg hover:bg-[#f3e8ff] transition-all duration-200 mb-4"
        >
          + New Chat
        </button>

        <div className="space-y-2 max-h-[70vh] overflow-y-auto pr-1 scrollbar-thin scrollbar-thumb-white/40 scrollbar-track-transparent">
          {chatTitles.map((chat) => (
            <div
              key={chat.id}
              className="flex items-center justify-between bg-white/10 hover:bg-white/20 rounded-lg px-3 py-2 text-sm truncate transition-all duration-150"
            >
              <Link
                to={`/chat/${chat.id}`}
                className="truncate flex-1 hover:underline"
              >
                {chat.title || 'Untitled Chat'}
              </Link>
              <button
                onClick={() => handleDelete(chat.id, chat.title)}
                className="ml-2 text-red-300 hover:text-red-500 transition"
                title="Delete chat"
              >
                <Trash2 size={16} />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Navbar;
