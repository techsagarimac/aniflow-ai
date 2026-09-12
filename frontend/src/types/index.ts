export type UserRole = "admin" | "production_manager" | "director" | "artist" | "reviewer";

export type User = {
  id: number;
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  avatar_color: string;
};

export type Project = {
  id: number;
  name: string;
  description: string;
  genre: string;
  studio: string;
  director_id: number | null;
  production_manager_id: number | null;
  start_date: string | null;
  target_completion_date: string | null;
  episode_count: number;
  status: string;
  director: User | null;
  production_manager: User | null;
  completed_episodes: number;
  overall_progress: number;
};

export type Episode = {
  id: number;
  project_id: number;
  number: number;
  title: string;
  description: string;
  target_release_date: string | null;
  status: string;
  progress: number;
  director: User | null;
  production_manager: User | null;
  scene_count: number;
  revision_count: number;
  risk_level: string | null;
  risk_score: number | null;
};

export type Character = {
  id: number;
  project_id: number;
  name: string;
  description: string;
  role: string;
};

export type Scene = {
  id: number;
  episode_id: number;
  scene_number: number;
  display_id: string;
  description: string;
  location: string;
  props: string[];
  duration_seconds: number;
  complexity: number;
  priority: string;
  assigned_artist_id: number | null;
  deadline: string | null;
  status: string;
  production_stage: string;
  kanban_column: string;
  revision_count: number;
  progress: number;
  assigned_artist: User | null;
  characters: Character[];
  episode_number: number | null;
  episode_title: string | null;
};

export type Task = {
  id: number;
  project_id: number | null;
  episode_id: number | null;
  scene_id: number | null;
  title: string;
  description: string;
  type: string;
  priority: string;
  status: string;
  assignee_id: number | null;
  start_date: string | null;
  deadline: string | null;
  estimated_hours: number;
  actual_hours: number;
  assignee: User | null;
  scene_display_id: string | null;
  episode_number: number | null;
};

export type Artist = {
  id: number;
  user_id: number;
  artist_role: string;
  skills: string[];
  experience_level: string;
  availability: string;
  avg_completion_hours: number;
  user: User | null;
  active_tasks: number;
  completed_tasks: number;
  workload_percent: number;
  deadline_risk: string;
};

export type Review = {
  id: number;
  scene_id: number;
  file_version_id: number | null;
  reviewer_id: number;
  status: string;
  comments: string;
  created_at: string;
  reviewer: User | null;
};

export type Revision = {
  id: number;
  scene_id: number;
  review_id: number | null;
  issue: string;
  priority: string;
  comment: string;
  assigned_to_id: number | null;
  status: string;
  created_at: string;
  assigned_to: User | null;
  created_by: User | null;
};

export type FileVersion = {
  id: number;
  file_id: number;
  scene_id: number | null;
  version_number: number;
  label: string;
  mime_type: string;
  size_bytes: number;
  notes: string;
  artist_id: number | null;
  review_status: string;
  created_at: string;
  artist: User | null;
  download_url: string | null;
};

export type Comment = {
  id: number;
  scene_id: number;
  user_id: number;
  body: string;
  created_at: string;
  user: User | null;
};

export type Notification = {
  id: number;
  type: string;
  title: string;
  message: string;
  is_read: boolean;
  related_entity_type: string | null;
  related_entity_id: number | null;
  created_at: string;
};

export type Milestone = {
  id: number;
  project_id: number;
  episode_id: number | null;
  scene_id: number | null;
  title: string;
  due_date: string;
  type: string;
  status: string;
};

export type DashboardData = {
  project_id: number;
  metrics: {
    total_episodes: number;
    completed_episodes: number;
    episodes_in_production: number;
    overall_progress: number;
    total_scenes: number;
    completed_scenes: number;
    scenes_in_production: number;
    overdue_scenes: number;
  };
  stage_progress: Record<string, { count: number; percent: number }>;
  artist_workload: Array<{
    user_id: number;
    name: string;
    role: string;
    avatar_color: string;
    active_tasks: number;
    workload_percent: number;
    deadline_risk: string;
  }>;
  bottlenecks: Array<{
    episode_id: number;
    episode_number: number;
    episode_title: string;
    risk_level: string;
    risk_score: number;
    reason: string;
    predicted_delay: string;
    recommendations: string[];
    requires_manager_approval: boolean;
  }>;
  upcoming_deadlines: Milestone[];
  episodes: Array<{ id: number; number: number; title: string; status: string; progress: number }>;
};

export type CalendarEvent = {
  id: string;
  title: string;
  date: string;
  type: string;
  status: string;
  entity_type: string;
  entity_id: number;
  scene_id?: number;
  episode_id?: number;
  priority?: string;
};

export const KANBAN_COLUMNS = [
  { key: "backlog", label: "Backlog" },
  { key: "storyboard", label: "Storyboard" },
  { key: "animation", label: "Animation" },
  { key: "color", label: "Color" },
  { key: "compositing", label: "Compositing" },
  { key: "qc", label: "QC" },
  { key: "completed", label: "Completed" },
] as const;
