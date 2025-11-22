
import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Button } from "@/shared/components/ui/button";
import { LayoutDashboard, Search, TrendingUp, BarChart3, Activity, Info, ChevronLeft, ChevronRight } from "lucide-react";
import { MarketCountdown } from "@/shared/components/MarketCountdown";

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
      <div className={`fixed left-0 top-0 h-full bg-gradient-to-b from-white to-gray-50/30 shadow-2xl border-r border-gray-200/50 backdrop-blur-sm transition-all duration-300 z-40 ${isSidebarOpen ? "w-64" : "w-16"}`}>
        {/* Header */}
        <div className="p-5 border-b border-blue-400/10 bg-gradient-to-br from-blue-600 via-indigo-600 to-blue-700 shadow-lg">
          <div className="flex items-center justify-between">
            {isSidebarOpen ? (
              <div className="flex-1">
                <h1 className="font-bold text-xl text-white leading-tight tracking-tight">
                  Stock Market
                </h1>
                <p className="text-blue-100 text-xs mt-0.5 font-medium">Sentiment Dashboard</p>
              </div>
            ) : (
              <div className="w-8 h-8 rounded-lg bg-white/20 flex items-center justify-center">
                <LayoutDashboard className="h-4 w-4 text-white" />
              </div>
            )}
            <Button 
              variant="ghost" 
              size="icon" 
              onClick={() => setIsSidebarOpen(!isSidebarOpen)} 
              className="text-white hover:bg-white/20 hover:text-white transition-all hover:scale-110"
            >
              {isSidebarOpen ? <ChevronLeft className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
            </Button>
          </div>
        </div>
        
        {/* Market Status - Prominent in Sidebar */}
        {isSidebarOpen && (
          <div className="px-3 pt-4 pb-3">
            <div className="relative">
              <div className="absolute inset-0 bg-gradient-to-br from-blue-400/20 to-indigo-400/20 rounded-xl blur-sm"></div>
              <div className="relative bg-gradient-to-br from-white via-blue-50/50 to-indigo-50 border border-blue-200/80 rounded-xl p-3.5 shadow-md hover:shadow-lg transition-all">
                <MarketCountdown variant="detailed" />
              </div>
            </div>
          </div>
        )}
        {!isSidebarOpen && (
          <div className="flex justify-center py-4 px-2">
            <MarketCountdown variant="compact" />
          </div>
        )}
        
        {/* Navigation */}
        <nav className="flex-1 px-3 py-3 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.href;
            return (
              <Link key={item.name} to={item.href}>
                <div className={`group relative ${
                  !isSidebarOpen ? "flex justify-center" : ""
                }`}>
                  {isActive && isSidebarOpen && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 bg-gradient-to-b from-blue-600 to-indigo-600 rounded-r-full"></div>
                  )}
                  <Button 
                    variant="ghost"
                    className={`w-full transition-all duration-200 ${
                      !isSidebarOpen 
                        ? "px-0 w-12 h-12 justify-center rounded-xl" 
                        : "justify-start px-4 py-2.5 rounded-xl"
                    } ${
                      isActive 
                        ? "bg-gradient-to-r from-blue-600 to-indigo-600 text-white shadow-lg hover:shadow-xl hover:from-blue-700 hover:to-indigo-700 scale-105" 
                        : "text-gray-700 hover:bg-gradient-to-r hover:from-blue-50 hover:to-indigo-50 hover:text-blue-700 hover:scale-105"
                    }`}
                  >
                    <Icon className={`h-5 w-5 ${
                      isSidebarOpen ? "mr-3" : ""
                    } ${
                      isActive ? "text-white" : "group-hover:scale-110 transition-transform"
                    }`} />
                    {isSidebarOpen && (
                      <span className="font-medium text-sm">{item.name}</span>
                    )}
                  </Button>
                </div>
              </Link>
            );
          })}
        </nav>

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
