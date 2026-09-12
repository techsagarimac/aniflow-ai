import { createContext, createElement, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api } from "../services/api";
import type { Project } from "../types";

type Ctx = {
  projects: Project[];
  projectId: number | null;
  setProjectId: (id: number) => void;
  refresh: () => Promise<void>;
};

const ProjectContext = createContext<Ctx | null>(null);

export function ProjectProvider({ children }: { children: ReactNode }) {
  const [projects, setProjects] = useState<Project[]>([]);
  const [projectId, setProjectIdState] = useState<number | null>(() => {
    const stored = localStorage.getItem("aniflow_project");
    return stored ? Number(stored) : null;
  });

  const refresh = async () => {
    const rows = await api.get<Project[]>("/api/projects");
    setProjects(rows);
    setProjectIdState((current) => {
      if (current && rows.some((p) => p.id === current)) return current;
      return rows[0]?.id ?? null;
    });
  };

  useEffect(() => {
    refresh().catch(() => setProjects([]));
  }, []);

  useEffect(() => {
    if (projectId) localStorage.setItem("aniflow_project", String(projectId));
  }, [projectId]);

  const setProjectId = (id: number) => setProjectIdState(id);
  const value = useMemo(() => ({ projects, projectId, setProjectId, refresh }), [projects, projectId]);
  return createElement(ProjectContext.Provider, { value }, children);
}

export function useProject() {
  const ctx = useContext(ProjectContext);
  if (!ctx) throw new Error("ProjectProvider missing");
  return ctx;
}
