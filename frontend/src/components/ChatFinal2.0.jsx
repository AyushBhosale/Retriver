import React, { useState, useEffect } from 'react';
import { useParams } from 'react-router-dom';
import { Paperclip, Send, X, File } from 'lucide-react';
import { apiClient } from '../utils/api';

const ChatFinal2 = () => {
  const { conversationId } = useParams(); // <-- From URL
  const [conversationIdState, setConversationId] = useState(null); // Local state copy
  const [messages, setMessages] = useState([{ text: 'Hello, how can I help you?', sender: 'bot' }]);
  const [input, setInput] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [isUploading, setIsUploading] = useState(false);

  // Fetch messages when conversationId is present
  useEffect(() => {
  if (conversationId) {
    const id = parseInt(conversationId);
    setConversationId(id);

    const fetchMessages = async () => {
      const token = localStorage.getItem('token');
      try {
        const res = await apiClient.get(`/rag/getMessages?conId=${id}`, {
          headers: { Authorization: `Bearer ${token}` },
        });

        // ✅ Map API response to internal format { text, sender }
        const loadedMessages = res.data.data.map((msg) => ({
          text: msg.content,
          sender: msg.sender === 'ai' ? 'bot' : 'user',
        }));

        setMessages(loadedMessages);
      } catch (err) {
        console.error('Failed to load messages:', err);
        setMessages([{ text: 'Failed to load messages.', sender: 'bot' }]);
      }
    };

    fetchMessages();
  }
}, [conversationId]);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) setSelectedFile(file);
  };

  const handleSubmit = async () => {
    if (!input && !selectedFile) return;

    const token = localStorage.getItem('token');
    setIsUploading(true);

    if (selectedFile) {
      const userMessage = { text: selectedFile.name, sender: 'user' };
      setMessages((prev) => [...prev, userMessage]);

      try {
        const formData = new FormData();
        formData.append('file', selectedFile);

        const res = await apiClient.post('/rag/upload', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
            Authorization: `Bearer ${token}`,
          },
        });

        const botMessage = {
          text: res.data?.message || 'File uploaded successfully.',
          sender: 'bot',
        };
        setMessages((prev) => [...prev, botMessage]);

        // Set conversation ID if returned from API
        if (res.data?.conversation_id) {
          setConversationId(res.data.conversation_id);
        }
      } catch (err) {
        setMessages((prev) => [
          ...prev,
          { text: 'Upload failed: ' + err.message, sender: 'bot' },
        ]);
      } finally {
        setSelectedFile(null);
      }
    }

    if (input) {
      const userMessage = { text: input, sender: 'user' };
      setMessages((prev) => [...prev, userMessage]);

      try {
        const res = await apiClient.post(
          '/rag/query',
          {
            question: input,
            conversation_id: conversationIdState,
          },
          {
            headers: { Authorization: `Bearer ${token}` },
          }
        );

        const botMessage = {
          text: res.data?.answer || 'No response received.',
          sender: 'bot',
        };
        setMessages((prev) => [...prev, botMessage]);
      } catch (err) {
        setMessages((prev) => [
          ...prev,
          { text: 'Query failed: ' + err.message, sender: 'bot' },
        ]);
      } finally {
        setInput('');
      }
    }

    setIsUploading(false);
  };

  return (
    <div className="w-full max-w-5xl mx-auto p-6 space-y-6">
      <div className="h-[80vh] overflow-y-auto bg-gray-50 rounded-2xl p-6 shadow-md space-y-4">
        {messages.map((msg, i) => (
          <div
            key={i}
            className={`p-3 rounded-xl max-w-[75%] text-sm ${
              msg.sender === 'bot'
                ? 'bg-blue-100 self-start'
                : 'bg-green-100 self-end ml-auto'
            }`}
          >
            {msg.text}
          </div>
        ))}
      </div>

      <div className="flex items-center gap-3">
        <input
          type="text"
          placeholder="Ask a question..."
          className="flex-1 p-3 border rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          disabled={isUploading}
        />

        <label className="cursor-pointer">
          <Paperclip className="w-6 h-6 text-gray-600" />
          <input type="file" className="hidden" onChange={handleFileChange} />
        </label>

        {selectedFile && (
          <div className="flex items-center space-x-2 bg-[#A56ABD] px-2 py-1 rounded-xl text-sm">
            <File className="w-4 h-4" />
            <span>{selectedFile.name}</span>
            <button onClick={() => setSelectedFile(null)}>
              <X className="w-4 h-4 text-red-500" />
            </button>
          </div>
        )}

        <button
          onClick={handleSubmit}
          className="bg-[#6E3482] text-white px-5 py-2 rounded-xl hover:bg-[#A56ABD] shadow-md"
          disabled={isUploading}
        >
          <Send className="w-5 h-5" />
        </button>
      </div>
    </div>
  );
};

export default ChatFinal2;
