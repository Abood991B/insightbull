
import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { 
  LayoutDashboard, 
  Search, 
  ChevronDown,
  ChevronUp,
  LogOut
} from "lucide-react";

interface AdminLayoutProps {
  children: React.ReactNode;
}

const AdminLayout = ({ children }: AdminLayoutProps) => {
  const location = useLocation();
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);

  const navigation = [
    { name: "Admin Dashboard", href: "/admin", icon: LayoutDashboard },
    { name: "Model Accuracy", href: "/admin/model-accuracy", icon: Search },
    { name: "API Configuration", href: "/admin/api-config", icon: LayoutDashboard },
    { name: "Watchlist Manager", href: "/admin/watchlist", icon: LayoutDashboard },
    { name: "Storage Settings", href: "/admin/storage", icon: LayoutDashboard },
    { name: "System Logs", href: "/admin/logs", icon: LayoutDashboard },
  ];

  const handleLogout = () => {
    localStorage.removeItem('adminAuthenticated');
    navigate('/admin/login');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-50">
      {/* Sidebar */}
      <div className={`fixed left-0 top-0 h-full bg-white shadow-lg transition-all duration-300 z-40 ${
        isSidebarOpen ? "w-64" : "w-16"
      }`}>
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            <h1 className={`font-bold text-xl text-red-600 transition-opacity ${
              isSidebarOpen ? "opacity-100" : "opacity-0"
            }`}>
              Admin Panel
            </h1>
            <Button
              variant="ghost"
              size="icon"
              onClick={() => setIsSidebarOpen(!isSidebarOpen)}
              className="ml-auto"
            >
              {isSidebarOpen ? <ChevronUp /> : <ChevronDown />}
            </Button>
          </div>
        </div>
        
        <nav className="p-4 space-y-2">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;
            
            return (
              <Link key={item.name} to={item.href}>
                <Button
                  variant={isActive ? "default" : "ghost"}
                  className={`w-full justify-start ${!isSidebarOpen && "px-2"}`}
                >
                  <Icon className="h-4 w-4" />
                  {isSidebarOpen && <span className="ml-2">{item.name}</span>}
                </Button>
              </Link>
            );
          })}
          
          <Button
            variant="ghost"
            className={`w-full justify-start text-red-600 hover:text-red-700 hover:bg-red-50 ${!isSidebarOpen && "px-2"}`}
            onClick={handleLogout}
          >
            <LogOut className="h-4 w-4" />
            {isSidebarOpen && <span className="ml-2">Logout</span>}
          </Button>
        </nav>
      </div>

      {/* Main Content */}
      <div className={`transition-all duration-300 ${
        isSidebarOpen ? "ml-64" : "ml-16"
      }`}>
        <div className="p-6">
          {children}
        </div>
      </div>
    </div>
  );
};

export default AdminLayout;
