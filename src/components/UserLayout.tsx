
import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { LayoutDashboard, Search, TrendingUp, BarChart3, Activity, Info, ChevronLeft, ChevronRight } from "lucide-react";

interface UserLayoutProps {
  children: React.ReactNode;
}

const UserLayout = ({ children }: UserLayoutProps) => {
  const location = useLocation();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  
  const navigation = [
    {
      name: "Dashboard",
      href: "/",
      icon: LayoutDashboard
    },
    {
      name: "Stock Analysis",
      href: "/analysis",
      icon: Search
    },
    {
      name: "Sentiment vs Price",
      href: "/sentiment-vs-price",
      icon: TrendingUp
    },
    {
      name: "Correlation Analysis",
      href: "/correlation",
      icon: BarChart3
    },
    {
      name: "Sentiment Trends",
      href: "/trends",
      icon: Activity
    },
    {
      name: "About",
      href: "/about",
      icon: Info
    }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Sidebar */}
      <div className={`fixed left-0 top-0 h-full bg-white shadow-xl border-r border-gray-200 transition-all duration-300 z-40 ${isSidebarOpen ? "w-64" : "w-16"}`}>
        {/* Header */}
        <div className="p-4 border-b border-gray-200 bg-gradient-to-r from-blue-600 to-blue-700">
          <div className="flex items-center justify-between">
            <div className={`transition-opacity duration-300 ${isSidebarOpen ? "opacity-100" : "opacity-0"}`}>
              <h1 className="font-bold text-lg text-white leading-tight">
                Stock Market
              </h1>
              <p className="text-blue-100 text-sm">Sentiment Dashboard</p>
            </div>
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)} 
              className="text-white hover:bg-blue-500/20 hover:text-white"
            >
              {isSidebarOpen ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </Button>
          </div>
        </div>
        
        {/* Navigation */}
        <nav className="p-4 space-y-2">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;
            return (
              <Link key={item.name} to={item.href}>
                <Button 
                  variant={isActive ? "default" : "ghost"} 
                  className={`w-full justify-start transition-all duration-200 ${
                    !isSidebarOpen ? "px-2" : ""
                  } ${
                    isActive 
                      ? "bg-blue-600 text-white shadow-sm hover:bg-blue-700" 
                      : "text-gray-700 hover:bg-gray-100 hover:text-gray-900"
                  }`}
                >
                  <Icon className={`h-4 w-4 ${isSidebarOpen ? "mr-3" : ""}`} />
                  {isSidebarOpen && (
                    <span className="font-medium">{item.name}</span>
                  )}
                </Button>
              </Link>
            );
          })}
        </nav>

        {/* Footer */}
        {isSidebarOpen && (
          <div className="absolute bottom-4 left-4 right-4">
            <div className="bg-gradient-to-r from-gray-50 to-gray-100 rounded-lg p-3 border">
              <p className="text-xs text-gray-600 font-medium">Real-time Data</p>
              <p className="text-xs text-gray-500">Last updated: Live</p>
            </div>
          </div>
        )}
      </div>

      {/* Main Content */}
      <div className={`transition-all duration-300 ${isSidebarOpen ? "ml-64" : "ml-16"}`}>
        <div className="p-6">
          {children}
        </div>
      </div>
    </div>
  );
};

export default UserLayout;
