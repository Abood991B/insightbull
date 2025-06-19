import { useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { LayoutDashboard, Search, ChevronDown, ChevronUp } from "lucide-react";
interface UserLayoutProps {
  children: React.ReactNode;
}
const UserLayout = ({
  children
}: UserLayoutProps) => {
  const location = useLocation();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const navigation = [{
    name: "Dashboard",
    href: "/",
    icon: LayoutDashboard
  }, {
    name: "Stock Analysis",
    href: "/analysis",
    icon: Search
  }, {
    name: "Sentiment vs Price",
    href: "/sentiment-vs-price",
    icon: LayoutDashboard
  }, {
    name: "Correlation Analysis",
    href: "/correlation",
    icon: LayoutDashboard
  }, {
    name: "Sentiment Trends",
    href: "/trends",
    icon: LayoutDashboard
  }, {
    name: "About",
    href: "/about",
    icon: LayoutDashboard
  }];
  return <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      {/* Sidebar */}
      <div className={`fixed left-0 top-0 h-full bg-white shadow-lg transition-all duration-300 z-40 ${isSidebarOpen ? "w-64" : "w-16"}`}>
        <div className="p-4 border-b">
          <div className="flex items-center justify-between">
            <h1 className={`font-bold text-xl text-blue-600 transition-opacity ${isSidebarOpen ? "opacity-100" : "opacity-0"}`}>Stock Market Sentiment Dashboard</h1>
            <Button variant="ghost" size="icon" onClick={() => setIsSidebarOpen(!isSidebarOpen)} className="ml-auto">
              {isSidebarOpen ? <ChevronUp /> : <ChevronDown />}
            </Button>
          </div>
        </div>
        
        <nav className="p-4 space-y-2">
          {navigation.map(item => {
          const Icon = item.icon;
          const isActive = location.pathname === item.href;
          return <Link key={item.name} to={item.href}>
                <Button variant={isActive ? "default" : "ghost"} className={`w-full justify-start ${!isSidebarOpen && "px-2"}`}>
                  <Icon className="h-4 w-4" />
                  {isSidebarOpen && <span className="ml-2">{item.name}</span>}
                </Button>
              </Link>;
        })}
        </nav>
      </div>

      {/* Main Content */}
      <div className={`transition-all duration-300 ${isSidebarOpen ? "ml-64" : "ml-16"}`}>
        <div className="p-6">
          {children}
        </div>
      </div>
    </div>;
};
export default UserLayout;