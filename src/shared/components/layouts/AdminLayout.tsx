import { useState, useEffect } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/shared/components/ui/button";
import { Badge } from "@/shared/components/ui/badge";
import { 
  LayoutDashboard, 
  Settings, 
  Database, 
  Activity, 
  FileText, 
  Users, 
  ChevronLeft, 
  ChevronRight,
  LogOut,
  Shield,
  Clock
} from "lucide-react";
import { authService } from "@/features/admin/services/auth.service";
import { useToast } from "@/shared/hooks/use-toast";

interface AdminLayoutProps {
  children: React.ReactNode;
}

const AdminLayout = ({ children }: AdminLayoutProps) => {
  const location = useLocation();
  const navigate = useNavigate();
  const { toast } = useToast();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [session, setSession] = useState<any>(null);
  const [timeRemaining, setTimeRemaining] = useState<string>("");

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
  
  const navigation = [
    {
      name: "Dashboard",
      href: "/admin/dashboard",
      icon: LayoutDashboard
    },
    {
      name: "Model Accuracy",
      href: "/admin/model-accuracy",
      icon: Activity
    },
    {
      name: "API Configuration",
      href: "/admin/api-config",
      icon: Settings
    },
    {
      name: "Watchlist Manager",
      href: "/admin/watchlist",
      icon: Users
    },
    {
      name: "Scheduler Manager",
      href: "/admin/scheduler",
      icon: Clock
    },
    {
      name: "Storage Settings",
      href: "/admin/storage",
      icon: Database
    },
    {
      name: "System Logs",
      href: "/admin/logs",
      icon: FileText
    }
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <div className={`${isSidebarOpen ? 'w-64' : 'w-16'} bg-white shadow-lg transition-all duration-300 ease-in-out flex flex-col`}>
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b">
          {isSidebarOpen && (
            <h1 className="text-xl font-bold text-gray-800">Admin Panel</h1>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2"
          >
            {isSidebarOpen ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-2">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;
            
            return (
              <Link
                key={item.name}
                to={item.href}
                className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                }`}
              >
                <Icon className="h-5 w-5 mr-3 flex-shrink-0" />
                {isSidebarOpen && <span>{item.name}</span>}
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        <div className="p-4 border-t space-y-2">
          {session && isSidebarOpen && (
            <div className="px-3 py-2 space-y-1">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <Shield className="h-4 w-4 text-green-600" />
                  <span className="text-xs font-medium">Secure Session</span>
                </div>
                <Badge variant="outline" className="text-xs">
                  <Clock className="h-3 w-3 mr-1" />
                  {timeRemaining}
                </Badge>
              </div>
              <p className="text-xs text-gray-500 truncate">{session?.user?.email}</p>
            </div>
          )}
          <Button
            onClick={handleLogout}
            variant="outline"
            className="w-full justify-start text-red-600 hover:bg-red-50 hover:text-red-700"
          >
            <LogOut className="h-5 w-5 mr-3 flex-shrink-0" />
            {isSidebarOpen && <span>Secure Logout</span>}
          </Button>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Bar */}
        <header className="bg-white shadow-sm border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-semibold text-gray-800">
              Admin Dashboard
            </h2>
            <div className="flex items-center space-x-4">
              {session && (
                <div className="flex items-center space-x-3">
                  <Badge variant="outline" className="text-xs">
                    <Shield className="h-3 w-3 mr-1 text-green-600" />
                    2FA Verified
                  </Badge>
                  <span className="text-sm text-gray-500">
                    {session.user?.name || session.user?.email}
                  </span>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-y-auto p-6">
          {children}
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;