import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { BrowserRouter, Route, Routes } from 'react-router';

import RequireAuth from './components/layout/RequireAuth.tsx';
import { AuthProvider } from './context/AuthContext.tsx';
import { ProfileDetailsProvider } from './context/ProfileDetailsContext.tsx';

import './index.css';
import AllColleaguesPage from './pages/AllColleaguesPage.tsx';
import FeedbackPage from './pages/FeedbackPage.tsx';
import LandingPage from './pages/LandingPage.tsx';
import LoginPage from './pages/LoginPage.tsx';
import MatchesPage from './pages/MatchesPage.tsx';
import ProfilePage from './pages/ProfilePage.tsx';
import PublicProfilePage from './pages/PublicProfilePage.tsx';
import RegisterPage from './pages/RegisterPage.tsx';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AuthProvider>
      <ProfileDetailsProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route
              path="/matches"
              element={
                <RequireAuth>
                  <MatchesPage />
                </RequireAuth>
              }
            />
            <Route
              path="/colleagues"
              element={
                <RequireAuth>
                  <AllColleaguesPage />
                </RequireAuth>
              }
            />
            <Route
              path="/profile"
              element={
                <RequireAuth>
                  <ProfilePage />
                </RequireAuth>
              }
            />
            <Route
              path="/profile/:id"
              element={
                <RequireAuth>
                  <PublicProfilePage />
                </RequireAuth>
              }
            />
            <Route
              path="/feedback"
              element={
                <RequireAuth>
                  <FeedbackPage />
                </RequireAuth>
              }
            />
          </Routes>
        </BrowserRouter>
      </ProfileDetailsProvider>
    </AuthProvider>
  </StrictMode>,
);