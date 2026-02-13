/*
 * InsightBull
 * Copyright (C) 2025-2026 Abdulrahman Baidaq
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program. If not, see <https://www.gnu.org/licenses/>.
 */

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
  SystemLogs,
  SchedulerManagerV2 // Using new V2 version with smart presets
} from "@/features/admin";
import OAuth2AdminAuth from "@/features/admin/components/OAuth2AdminAuth";
import AdminProtectedRoute from "@/features/admin/components/AdminProtectedRoute";

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
          <Route path="/admin" element={<AdminLogin />} />
          <Route path="/admin/auth/callback" element={<OAuth2AdminAuth />} />
          <Route path="/admin/dashboard" element={
            <AdminProtectedRoute>
              <AdminDashboard />
            </AdminProtectedRoute>
          } />
          <Route path="/admin/model-accuracy" element={
            <AdminProtectedRoute>
              <ModelAccuracy />
            </AdminProtectedRoute>
          } />
          <Route path="/admin/api-config" element={
            <AdminProtectedRoute>
              <ApiConfig />
            </AdminProtectedRoute>
          } />
          <Route path="/admin/watchlist" element={
            <AdminProtectedRoute>
              <WatchlistManager />
            </AdminProtectedRoute>
          } />
          <Route path="/admin/scheduler" element={
            <AdminProtectedRoute>
              <SchedulerManagerV2 />
            </AdminProtectedRoute>
          } />
          <Route path="/admin/storage" element={
            <AdminProtectedRoute>
              <StorageSettings />
            </AdminProtectedRoute>
          } />
          <Route path="/admin/logs" element={
            <AdminProtectedRoute>
              <SystemLogs />
            </AdminProtectedRoute>
          } />
          
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
