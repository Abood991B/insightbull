import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService, AuthSession } from '../services/auth.service';
import { Button } from '@/shared/components/ui/button';
import { Badge } from '@/shared/components/ui/badge';
import { LogOut, Shield, Clock, User } from 'lucide-react';
import { useToast } from '@/shared/hooks/use-toast';

interface AdminSecurityManagerProps {
  children?: React.ReactNode;
}

const AdminSecurityManager = ({ children }: AdminSecurityManagerProps) => {
  const navigate = useNavigate();
  const { toast } = useToast();
  const [session, setSession] = useState<AuthSession | null>(null);
  const [timeRemaining, setTimeRemaining] = useState<string>('');

  useEffect(() => {
    // Update session info
    const updateSession = () => {
      const currentSession = authService.getSession();
      setSession(currentSession);
      
      if (currentSession) {
        // Calculate time remaining
        const remaining = currentSession.expiresAt - Date.now();
        const minutes = Math.floor(remaining / 60000);
        const seconds = Math.floor((remaining % 60000) / 1000);
        setTimeRemaining(`${minutes}:${seconds.toString().padStart(2, '0')}`);
        
        // Warn when session is about to expire
        if (remaining < 300000 && remaining > 295000) { // 5 minutes warning
          toast({
            title: "Session Expiring Soon",
            description: "Your session will expire in 5 minutes. Please save your work.",
            variant: "default",
          });
        }
      }
    };

    updateSession();
    const interval = setInterval(updateSession, 1000);
    
    return () => clearInterval(interval);
  }, [toast]);

  const handleLogout = () => {
    authService.logout();
    toast({
      title: "Logged Out",
      description: "You have been securely logged out.",
    });
    navigate('/admin');
  };

  if (!session) {
    return null;
  }

  return (
    <div className="fixed top-0 right-0 z-50 p-4">
      <div className="bg-white rounded-lg shadow-lg border border-gray-200 p-4 min-w-[300px]">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <Shield className="h-4 w-4 text-green-600" />
            <span className="text-sm font-medium">Secure Session</span>
          </div>
          <Badge variant="outline" className="text-xs">
            <Clock className="h-3 w-3 mr-1" />
            {timeRemaining}
          </Badge>
        </div>
        
        <div className="space-y-2 mb-3">
          <div className="flex items-center space-x-2">
            <User className="h-3 w-3 text-gray-500" />
            <span className="text-xs text-gray-600">{session.user.email}</span>
          </div>
          <div className="flex items-center space-x-2">
            <Badge className="text-xs" variant={session.totpVerified ? "default" : "secondary"}>
              2FA: {session.totpVerified ? "Verified" : "Pending"}
            </Badge>
          </div>
        </div>
        
        <Button
          variant="outline"
          size="sm"
          onClick={handleLogout}
          className="w-full"
        >
          <LogOut className="h-3 w-3 mr-2" />
          Secure Logout
        </Button>
      </div>
      {children}
    </div>
  );
};

export default AdminSecurityManager;
