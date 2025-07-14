import React from 'react'
import { useState } from 'react'
import { apiClient } from '../utils/api'
import { useNavigate } from 'react-router-dom'
const Login = () => {
  const navigate = useNavigate();
  const [password, setPassword] = useState('')
  const [username, setUsername] = useState('')
  const handleClick = (e) => {
    e.preventDefault()
    const formData = new URLSearchParams();
    formData.append('username',username)
    formData.append('password',password)
    apiClient.post('/auth/token', formData, {
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    }).then((response)=>{
        const token = response.data.access_token;
        localStorage.setItem('token', token);
        console.log(token)
        navigate('/')
    }).catch((error)=>{
        console.error(error);
    });
  }
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="w-full max-w-md bg-white p-8 rounded-xl shadow-md">
        <h1 className="text-2xl font-bold text-center mb-6">Login</h1>
        <form>
          <input
            type="text"
            name="username"
            placeholder="Username"
            className="w-full px-4 py-2 mb-4 shadow-md rounded-md focus:outline-none focus:ring-2 focus:ring-gray-700"
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            type="password"
            name="password"
            placeholder="Password"
            className="w-full px-4 py-2 mb-6 shadow-md rounded-md focus:outline-none focus:ring-2 focus:ring-gray-700"
            onChange={(e) => setPassword(e.target.value)}
          />
          <button
            type="submit"
            onClick={handleClick}
            className="w-full bg-[#6E3482] hover:bg-[#A56ABD] text-white font-semibold py-2 rounded-md transition duration-200"
          >
            Login
          </button>
        </form>
      </div>
    </div>
  )
}

export default Login
