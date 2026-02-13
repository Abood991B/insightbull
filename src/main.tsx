/*
 * Insight Stock Dashboard
 * Copyright (C) 2025-2026 Abdulrahman Baidaq
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <https://www.gnu.org/licenses/>.
 */

import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './styles/index.css'
import { initializeSecurity } from './features/admin/middleware/security.middleware'
import { validateSecurityConfig } from './features/admin/config/security.config'

if (window.location.pathname.startsWith('/admin')) {
  initializeSecurity();
  const isConfigValid = validateSecurityConfig();
  if (!isConfigValid && import.meta.env.DEV) {
    console.warn('⚠️ Security configuration issues detected. Check console for details.');
  }
}

createRoot(document.getElementById("root")!).render(<App />);
