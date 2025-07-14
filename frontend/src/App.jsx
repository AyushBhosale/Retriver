import './App.css';
import { Routes, Route } from 'react-router-dom';
import Home from './pages/home.jsx';
import Login from './pages/login.jsx';
import ChatFinal from './components/Chat.jsx';
import ChatFinal2 from './components/ChatFinal2.0.jsx';
import Navbar from './components/Navbar.jsx';

function App() {
  return (
    <div className="flex h-screen w-screen overflow-hidden"> {/* Full screen layout */}
      
      {/* Sidebar/Navbar */}
      <div className="w-64 h-full bg-gray-100 border-r shadow-md flex-shrink-0">
        <Navbar />
      </div>

      {/* Main Content Area */}
      <div className="flex-1 h-full overflow-y-auto bg-white">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/login" element={<Login />} />
          <Route path="/chat/:conversationId" element={<ChatFinal2 />} />
        </Routes>
      </div>
    </div>
  );
}

export default App;
