import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Layout from './components/Layout/Layout';
import Login from './pages/Login/Login';
import Register from './pages/Register/Register';
import Home from './pages/Home/Home';
import CreateTest from './pages/CreateTest/CreateTest';
import MyDocuments from './pages/MyDocuments/MyDocuments';
import MyTests from './pages/MyTests/MyTests';
import Profile from './pages/Profile/Profile';
import Chat from './pages/Chat/Chat';
import PropTypes from 'prop-types';
import './App.css';

const ProtectedRoute = ({ children }) => {
    const { isAuthenticated, loading } = useAuth();

    if (loading) {
        return <div className="loading">Загрузка...</div>;
    }

    return isAuthenticated ? children : <Navigate to="/login" />;
};

ProtectedRoute.propTypes = {
    children: PropTypes.node.isRequired
};

function App() {
    return (
        <AuthProvider>
            <Router>
                <div className="App">
                    <Routes>
                        <Route path="/login" element={<Login />} />
                        <Route path="/register" element={<Register />} />
                        <Route path="/" element={
                            <ProtectedRoute>
                                <Layout />
                            </ProtectedRoute>
                        }>
                            <Route index element={<Home />} />
                            <Route path="create-test" element={<CreateTest />} />
                            <Route path="my-documents" element={<MyDocuments />} />
                            <Route path="my-tests" element={<MyTests />} />
                            <Route path="profile" element={<Profile />} />
                            <Route path="chat" element={<Chat />} />
                        </Route>
                    </Routes>
                </div>
            </Router>
        </AuthProvider>
    );
}

export default App;
