import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../services/auth.service';
import OAuth2AdminAuth from '../components/OAuth2AdminAuth';

const AdminLogin = () => {
  const navigate = useNavigate();

  useEffect(() => {
    // Check if user is already authenticated
    if (authService.isFullyAuthenticated()) {
      navigate('/admin/dashboard', { replace: true });
    }
  }, [navigate]);

  return <OAuth2AdminAuth />;
};

export default AdminLogin;