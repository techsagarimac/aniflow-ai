import { Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import { ProjectProvider } from "./context/ProjectContext";
import { ToastProvider } from "./context/ToastContext";
import { AppLayout } from "./layouts/AppLayout";
import { LoadingState } from "./components/ui/Primitives";
import { LoginPage } from "./pages/LoginPage";
import { DashboardPage } from "./pages/DashboardPage";
import { ProjectDetailPage, ProjectsPage } from "./pages/ProjectsPage";
import { EpisodeDetailPage, EpisodesPage } from "./pages/EpisodesPage";
import { SceneDetailPage, ScenesPage } from "./pages/ScenesPage";
import { TasksPage } from "./pages/TasksPage";
import { ArtistDetailPage, ArtistsPage } from "./pages/ArtistsPage";
import { CalendarPage } from "./pages/CalendarPage";
import { ReviewsPage } from "./pages/ReviewsPage";
import { AssistantPage } from "./pages/AssistantPage";
import { AnalyticsPage } from "./pages/AnalyticsPage";
import { NotificationsPage, SettingsPage } from "./pages/NotificationsPage";
import type { ReactNode } from "react";

function Guard({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <LoadingState />;
  if (!user) return <Navigate to="/login" replace />;
  return <ProjectProvider>{children}</ProjectProvider>;
}

export default function App() {
  return (
    <ToastProvider>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <Guard>
                <AppLayout />
              </Guard>
            }
          >
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="projects" element={<ProjectsPage />} />
            <Route path="projects/:id" element={<ProjectDetailPage />} />
            <Route path="episodes" element={<EpisodesPage />} />
            <Route path="episodes/:id" element={<EpisodeDetailPage />} />
            <Route path="scenes" element={<ScenesPage />} />
            <Route path="scenes/:id" element={<SceneDetailPage />} />
            <Route path="tasks" element={<TasksPage />} />
            <Route path="artists" element={<ArtistsPage />} />
            <Route path="artists/:id" element={<ArtistDetailPage />} />
            <Route path="calendar" element={<CalendarPage />} />
            <Route path="reviews" element={<ReviewsPage />} />
            <Route path="assistant" element={<AssistantPage />} />
            <Route path="analytics" element={<AnalyticsPage />} />
            <Route path="notifications" element={<NotificationsPage />} />
            <Route path="settings" element={<SettingsPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </ToastProvider>
  );
}
