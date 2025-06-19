
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Index from "./pages/Index";
import StockAnalysis from "./pages/StockAnalysis";
import SentimentVsPrice from "./pages/SentimentVsPrice";
import CorrelationAnalysis from "./pages/CorrelationAnalysis";
import SentimentTrends from "./pages/SentimentTrends";
import About from "./pages/About";
import AdminDashboard from "./pages/admin/AdminDashboard";
import ModelAccuracy from "./pages/admin/ModelAccuracy";
import ApiConfig from "./pages/admin/ApiConfig";
import WatchlistManager from "./pages/admin/WatchlistManager";
import StorageSettings from "./pages/admin/StorageSettings";
import SystemLogs from "./pages/admin/SystemLogs";
import AdminLogin from "./pages/admin/AdminLogin";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          {/* User Routes */}
          <Route path="/" element={<Index />} />
          <Route path="/analysis" element={<StockAnalysis />} />
          <Route path="/sentiment-vs-price" element={<SentimentVsPrice />} />
          <Route path="/correlation" element={<CorrelationAnalysis />} />
          <Route path="/trends" element={<SentimentTrends />} />
          <Route path="/about" element={<About />} />
          
          {/* Admin Routes */}
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/model-accuracy" element={<ModelAccuracy />} />
          <Route path="/admin/api-config" element={<ApiConfig />} />
          <Route path="/admin/watchlist" element={<WatchlistManager />} />
          <Route path="/admin/storage" element={<StorageSettings />} />
          <Route path="/admin/logs" element={<SystemLogs />} />
          
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
