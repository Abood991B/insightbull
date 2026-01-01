import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './styles/index.css'
import { initializeSecurity } from './features/admin/middleware/security.middleware'
import { validateSecurityConfig } from './features/admin/config/security.config'

if (window.location.pathname.startsWith('/admin')) {
  initializeSecurity();
  const isConfigValid = validateSecurityConfig();
  if (!isConfigValid) {
    console.warn('⚠️ Security configuration issues detected. Check console for details.');
  }
}

createRoot(document.getElementById("root")!).render(<App />);
