import { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { authService } from '../services/auth.service';
import { Loader2 } from 'lucide-react';

interface AdminProtectedRouteProps {
  children: React.ReactNode;
}

const AdminProtectedRoute = ({ children }: AdminProtectedRouteProps) => {
  const [isChecking, setIsChecking] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const location = useLocation();

  useEffect(() => {
    checkAuthentication();
    
    // Set up periodic authentication check
    const interval = setInterval(checkAuthentication, 30000); // Check every 30 seconds
    
    return () => clearInterval(interval);
  }, []);

  const checkAuthentication = () => {
    const authenticated = authService.isFullyAuthenticated();
    setIsAuthenticated(authenticated);
    setIsChecking(false);
    
    if (authenticated) {
      // Update session activity on route change
      authService.updateSessionActivity();
    }
  };

  if (isChecking) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-900 to-gray-800 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 text-blue-500 animate-spin mx-auto mb-4" />
          <p className="text-white">Verifying authentication...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    // Redirect to admin auth page, preserving the intended destination
    return <Navigate to="/admin" state={{ from: location }} replace />;
  }

  return <>{children}</>;
};

export default AdminProtectedRoute;
