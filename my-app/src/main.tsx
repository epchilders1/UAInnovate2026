import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import './index.css'
import App from './App.tsx'
import { LoadingProvider } from './context/LoadingContext.tsx'
import { JarvisProvider } from './context/JarvisContext.tsx'
import { GoogleOAuthProvider } from '@react-oauth/google';
import LoginPage from './client-pages/LoginPage/LoginPage';
import ProtectedRoute from './middleware/ProtectedRoute.tsx';

const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: <ProtectedRoute><App /></ProtectedRoute>,
  },
]);

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <GoogleOAuthProvider clientId={import.meta.env.VITE_GOOGLE_CLIENT_ID}>
      <LoadingProvider>
        <JarvisProvider>
          <RouterProvider router={router} />
        </JarvisProvider>
      </LoadingProvider>
    </GoogleOAuthProvider>
  </StrictMode>,
)
