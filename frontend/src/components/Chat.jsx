import React, { useState } from 'react';
import { Paperclip, X, FileText, Image, File } from 'lucide-react';
// import { apiClient } from '../utils/api';
const ChatFinal = () => {
  const [messages, setMessages] = useState([
    { text: 'Hello, how can I help you?', sender: 'bot' }
  ]);
  const [input, setInput] = useState('');
  const [selectedFiles, setSelectedFiles] = useState([]);

  const handleSend = () => {
    if (input.trim() === '' && selectedFiles.length === 0) return;

    const newUserMessage = { 
      text: input, 
      sender: 'user',
      files: selectedFiles.length > 0 ? [...selectedFiles] : null
    };
    const staticBotReply = { text: 'I can see your message' + (selectedFiles.length > 0 ? ` and ${selectedFiles.length} file(s)` : '') + '. How can I help you?', sender: 'bot' };

    setMessages([...messages, newUserMessage, staticBotReply]);
    setInput('');
    setSelectedFiles([]);
  };

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files);
    const fileData = files.map(file => ({
      name: file.name,
      size: file.size,
      type: file.type,
      file: file
    }));
    setSelectedFiles([...selectedFiles, ...fileData]);
  };


  const removeFile = (index) => {
    setSelectedFiles(selectedFiles.filter((_, i) => i !== index));
  };

  const getFileIcon = (type) => {
    if (type.startsWith('image/')) return <Image size={16} />;
    if (type === 'application/pdf' || type.startsWith('text/')) return <FileText size={16} />;
    return <File size={16} />;
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <div className="flex flex-col h-screen flex-1 bg-gradient-to-b from-purple-100 to-white">
      {/* Chat Messages */}
      <div className="flex-1 p-4 overflow-y-auto flex flex-col">
        {messages.map((msg, idx) => (
          <div
            key={idx}
            className={`my-2 p-3 rounded-xl max-w-xs text-sm ${
              msg.sender === 'user'
                ? 'bg-white text-black self-start border border-gray-200'
                : 'bg-purple-600 text-white self-end'
            }`}
          >
            {msg.text}
            {msg.files && (
              <div className="mt-2 space-y-1">
                {msg.files.map((file, fileIdx) => (
                  <div key={fileIdx} className="flex items-center space-x-2 bg-gray-50 p-2 rounded border">
                    {getFileIcon(file.type)}
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-medium text-gray-700 truncate">{file.name}</p>
                      <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* File Preview Area */}
      {selectedFiles.length > 0 && (
        <div className="p-3 bg-gray-50 border-t">
          <div className="flex flex-wrap gap-2">
            {selectedFiles.map((file, index) => (
              <div key={index} className="flex items-center space-x-2 bg-white p-2 rounded border">
                {getFileIcon(file.type)}
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium text-gray-700 truncate">{file.name}</p>
                  <p className="text-xs text-gray-500">{formatFileSize(file.size)}</p>
                </div>
                <button
                  onClick={() => removeFile(index)}
                  className="text-gray-400 hover:text-red-500 transition-colors"
                >
                  <X size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Input Box */}
      <div className="flex p-3 border-t bg-white shadow-inner">
        <div className="flex items-center space-x-2 flex-1">
          <input
            type="file"
            multiple
            onChange={handleFileSelect}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="cursor-pointer p-2 text-purple-600 hover:text-purple-800 hover:bg-purple-50 rounded-full transition-colors"
          >
            <Paperclip size={20} />
          </label>
          <input
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSend()}
            placeholder="Type a message..."
            className="flex-1 px-4 py-2 border border-purple-300 rounded-full focus:outline-none focus:ring-2 focus:ring-purple-400"
          />
        </div>
        <button
          onClick={handleSend}
          className="ml-2 px-5 py-2 bg-purple-700 text-white rounded-full hover:bg-purple-800 transition-colors"
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatFinal;
