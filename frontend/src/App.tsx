import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { useAuthStore } from './stores/auth';
import { useTheme } from './stores/theme';
import { AuthLayout } from './layouts/AuthLayout';
import { AppLayout } from './layouts/AppLayout';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { DashboardPage } from './pages/DashboardPage';
import DatasetsPage from './pages/DatasetsPage';
import { TicketsPage } from './pages/TicketsPage';
import { InsightsPage } from './pages/InsightsPage';
import { AskPage } from './pages/AskPage';
import { HistoryPage } from './pages/HistoryPage';
import { SettingsPage } from './pages/SettingsPage';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
      staleTime: 30000,
    },
  },
});

function ProtectedRoute({ children, isAuthenticated }: { children: React.ReactNode; isAuthenticated: boolean }) {
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function PublicRoute({ children, isAuthenticated }: { children: React.ReactNode; isAuthenticated: boolean }) {
  if (isAuthenticated) return <Navigate to="/dashboard" replace />;
  return <>{children}</>;
}

export default function App() {
  const auth = useAuthStore();
  const { theme, toggleTheme } = useTheme();

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Toaster position="top-right" toastOptions={{
          className: 'dark:bg-gray-800 dark:text-white',
        }} />
        <Routes>
          <Route path="/login" element={
            <PublicRoute isAuthenticated={auth.isAuthenticated}>
              <AuthLayout>
                <LoginPage onLogin={auth.login} />
              </AuthLayout>
            </PublicRoute>
          } />
          <Route path="/register" element={
            <PublicRoute isAuthenticated={auth.isAuthenticated}>
              <AuthLayout>
                <RegisterPage onLogin={auth.login} />
              </AuthLayout>
            </PublicRoute>
          } />
          <Route path="/" element={
            <ProtectedRoute isAuthenticated={auth.isAuthenticated}>
              <AppLayout user={auth.user!} onLogout={auth.logout} theme={theme} onToggleTheme={toggleTheme} />
            </ProtectedRoute>
          }>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="datasets" element={<DatasetsPage />} />
            <Route path="datasets/:id/tickets" element={<TicketsPage />} />
            <Route path="datasets/:id/insights" element={<InsightsPage />} />
            <Route path="datasets/:id/ask" element={<AskPage />} />
            <Route path="history" element={<HistoryPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}
