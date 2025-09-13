
import { Toaster } from "@/shared/components/ui/toaster";
import { Toaster as Sonner } from "@/shared/components/ui/sonner";
import { TooltipProvider } from "@/shared/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";

// Feature imports
import { Index, About, NotFound } from "@/features/dashboard";
import { 
  StockAnalysis, 
  SentimentVsPrice, 
  CorrelationAnalysis, 
  SentimentTrends 
} from "@/features/analysis";
import { 
  AdminDashboard, 
  AdminLogin,
  ModelAccuracy, 
  ApiConfig, 
  WatchlistManager, 
  StorageSettings, 
  SystemLogs 
} from "@/features/admin";

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
