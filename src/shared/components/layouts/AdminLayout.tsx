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
  Clock,
  BarChart3,
  Zap,
  Server,
  AlertTriangle,
  TrendingUp,
  Cog
} from "lucide-react";
import { authService } from "@/features/admin/services/auth.service";
import { useToast } from "@/shared/hooks/use-toast";
import { MarketCountdown } from "@/shared/components/MarketCountdown";

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

  const getPageTitle = (pathname: string) => {
    const titles: { [key: string]: string } = {
      '/admin/dashboard': 'Comprehensive monitoring and management dashboard',
      '/admin/model-accuracy': 'Sentiment analysis performance metrics and evaluation',
      '/admin/api-config': 'External API keys and configuration management',
      '/admin/watchlist': 'Stock symbols monitoring and management',
      '/admin/scheduler': 'Automated tasks and job scheduling',
      '/admin/storage': 'Data retention policies and storage management',
      '/admin/logs': 'Application logs and system debugging'
    };
    return titles[pathname] || 'Advanced system administration tools';
  };

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
  
  const navigationSections = [
    {
      title: "Overview",
      items: [
        {
          name: "System Dashboard",
          href: "/admin/dashboard",
          icon: LayoutDashboard,
          description: "System overview and health monitoring"
        }
      ]
    },
    {
      title: "Analytics & Performance",
      items: [
        {
          name: "Model Accuracy",
          href: "/admin/model-accuracy",
          icon: BarChart3,
          description: "Sentiment analysis performance metrics"
        },
        {
          name: "System Logs",
          href: "/admin/logs",
          icon: FileText,
          description: "Application logs and debugging"
        }
      ]
    },
    {
      title: "Configuration",
      items: [
        {
          name: "API Configuration",
          href: "/admin/api-config",
          icon: Settings,
          description: "External API keys and settings"
        },
        {
          name: "Watchlist Manager",
          href: "/admin/watchlist",
          icon: TrendingUp,
          description: "Stock symbols monitoring"
        },
        {
          name: "Scheduler Manager",
          href: "/admin/scheduler",
          icon: Clock,
          description: "Automated tasks and jobs"
        }
      ]
    },
    {
      title: "System Management",
      items: [
        {
          name: "Storage Settings",
          href: "/admin/storage",
          icon: Database,
          description: "Data retention and cleanup"
        }
      ]
    }
  ];

  return (
    <div className="flex h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      {/* Enhanced Sidebar */}
      <div className={`${isSidebarOpen ? 'w-72' : 'w-16'} bg-white shadow-xl transition-all duration-300 ease-in-out flex flex-col border-r border-gray-200`}>
        {/* Enhanced Header */}
        <div className="flex items-center justify-between p-6 border-b border-gray-200 bg-gradient-to-r from-blue-600 to-indigo-600">
          {isSidebarOpen && (
            <div className="flex items-center space-x-3">
              <div className="p-2 bg-white/20 rounded-lg">
                <Server className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-white">Control Center</h1>
                <p className="text-xs text-blue-100">System Administration</p>
              </div>
            </div>
          )}
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsSidebarOpen(!isSidebarOpen)}
            className="p-2 text-white hover:bg-white/20"
          >
            {isSidebarOpen ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
          </Button>
        </div>

        {/* Market Status - Prominent in Admin Sidebar */}
        {isSidebarOpen && (
          <div className="mx-4 my-4">
            <div className="bg-gradient-to-br from-slate-50 to-blue-50 border border-blue-200/60 rounded-xl p-3.5 shadow-sm hover:shadow-md transition-shadow">
              <MarketCountdown variant="detailed" />
            </div>
          </div>
        )}
        {!isSidebarOpen && (
          <div className="flex justify-center py-4">
            <MarketCountdown variant="compact" />
          </div>
        )}

        {/* Enhanced Navigation */}
        <nav className="flex-1 p-4 space-y-6 overflow-y-auto">
          {navigationSections.map((section) => (
            <div key={section.title}>
              {isSidebarOpen && (
                <h3 className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-3 px-3">
                  {section.title}
                </h3>
              )}
              <div className="space-y-1">
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = location.pathname === item.href;
                  
                  return (
                    <Link
                      key={item.name}
                      to={item.href}
                      className={`group flex items-center px-3 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                        isActive
                          ? 'bg-gradient-to-r from-blue-500 to-indigo-500 text-white shadow-lg transform scale-105'
                          : 'text-gray-700 hover:bg-gray-100 hover:text-gray-900 hover:shadow-md'
                      }`}
                      title={isSidebarOpen ? undefined : item.name}
                    >
                      <div className={`p-2 rounded-lg mr-3 flex-shrink-0 ${
                        isActive 
                          ? 'bg-white/20' 
                          : 'bg-gray-100 group-hover:bg-gray-200'
                      }`}>
                        <Icon className={`h-4 w-4 ${
                          isActive ? 'text-white' : 'text-gray-600 group-hover:text-gray-700'
                        }`} />
                      </div>
                      {isSidebarOpen && (
                        <div className="flex-1 min-w-0">
                          <div className={`font-medium ${isActive ? 'text-white' : 'text-gray-900'}`}>
                            {item.name}
                          </div>
                          <div className={`text-xs mt-0.5 ${
                            isActive ? 'text-blue-100' : 'text-gray-500'
                          }`}>
                            {item.description}
                          </div>
                        </div>
                      )}
                      {isActive && isSidebarOpen && (
                        <div className="w-1 h-8 bg-white/30 rounded-full ml-2"></div>
                      )}
                    </Link>
                  );
                })}
              </div>
            </div>
          ))}
        </nav>

        {/* Enhanced Footer */}
        <div className="p-4 border-t border-gray-200 bg-gray-50 space-y-3">
          {session && isSidebarOpen && (
            <div className="px-3 py-3 bg-white rounded-lg border border-gray-200 shadow-sm">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-2">
                  <div className="p-1 bg-green-100 rounded-full">
                    <Shield className="h-3 w-3 text-green-600" />
                  </div>
                  <span className="text-xs font-semibold text-gray-700">Secure Session</span>
                </div>
                <Badge variant="outline" className="text-xs bg-blue-50 text-blue-700 border-blue-200">
                  <Clock className="h-3 w-3 mr-1" />
                  {timeRemaining}
                </Badge>
              </div>
              <div className="flex items-center space-x-2">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <p className="text-xs text-gray-600 truncate font-medium">{session?.user?.email}</p>
              </div>
            </div>
          )}
          <Button
            onClick={handleLogout}
            variant="outline"
            className="w-full justify-start text-red-600 hover:bg-red-50 hover:text-red-700 border-red-200 hover:border-red-300 transition-all duration-200"
          >
            <div className="p-1 bg-red-100 rounded-lg mr-3">
              <LogOut className="h-4 w-4 flex-shrink-0" />
            </div>
            {isSidebarOpen && <span className="font-medium">Secure Logout</span>}
          </Button>
        </div>
      </div>

      {/* Enhanced Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Enhanced Top Bar */}
        <header className="bg-white shadow-lg border-b border-gray-200 px-8 py-5">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-gradient-to-r from-blue-500 to-indigo-500 rounded-lg">
                  <Cog className="h-5 w-5 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">
                    System Administration
                  </h2>
                  <p className="text-sm text-gray-600">
                    {getPageTitle(location.pathname)}
                  </p>
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              {session && (
                <div className="flex items-center space-x-4">
                  <div className="flex items-center space-x-2">
                    <Badge className="bg-green-100 text-green-800 border-green-200">
                      <Shield className="h-3 w-3 mr-1" />
                      2FA Verified
                    </Badge>
                    <Badge className="bg-blue-100 text-blue-800 border-blue-200">
                      <Clock className="h-3 w-3 mr-1" />
                      {timeRemaining}
                    </Badge>
                  </div>
                  <div className="flex items-center space-x-2 px-3 py-2 bg-gray-50 rounded-lg border border-gray-200">
                    <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                    <span className="text-sm font-medium text-gray-700">
                      {session.user?.name || session.user?.email}
                    </span>
                  </div>
                </div>
              )}
            </div>
          </div>
        </header>

        {/* Enhanced Page Content */}
        <main className="flex-1 overflow-y-auto p-8 bg-gradient-to-br from-gray-50 to-gray-100">
          <div className="max-w-7xl mx-auto">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export default AdminLayout;