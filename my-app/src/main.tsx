import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { LoadingProvider } from './context/LoadingContext.tsx'
import { JarvisProvider } from './context/JarvisContext.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <LoadingProvider>
      <JarvisProvider>
        <App />
      </JarvisProvider>
    </LoadingProvider>
  </StrictMode>,
)
