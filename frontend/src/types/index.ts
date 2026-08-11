export type UserRole = 'CITIZEN' | 'EMPLOYEE' | 'MANAGER' | 'ADMIN';

export type ReportStatus =
  | 'SUBMITTED'
  | 'AI_ANALYZING'
  | 'UNDER_REVIEW'
  | 'CONFIRMED'
  | 'ASSIGNED'
  | 'IN_PROGRESS'
  | 'REPAIR_COMPLETED'
  | 'VERIFICATION'
  | 'RESOLVED'
  | 'REJECTED'
  | 'DUPLICATE'
  | 'CANNOT_VERIFY';

export type SeverityLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  phone_number?: string;
  avatar_url?: string;
  is_active: boolean;
  department_id?: string;
  created_at: string;
}

export interface Location {
  id: string;
  latitude: number;
  longitude: number;
  address: string;
  neighborhood?: string;
  city?: string;
  state?: string;
  zip_code?: string;
}

export interface VisionAnalysis {
  category: string;
  confidence: number;
  severity: SeverityLevel;
  damage_score: number;
  objects_detected: string[];
  reasoning: string;
}

export interface PriorityBreakdown {
  score: number;
  severity_level: SeverityLevel;
  visual_damage: number;
  location_risk: number;
  infrastructure_type: number;
  report_count: number;
  traffic_importance: number;
}

export interface Report {
  id: string | number;
  title: string;
  description?: string;
  category: string;
  status: ReportStatus;
  user_id?: string | number;
  latitude?: number;
  longitude?: number;
  address?: string;
  neighborhood?: string;
  location_id?: string | number;
  location?: Location;
  image_url?: string;
  image_urls?: string[];
  upvotes?: number;
  ai_score?: number;
  priority_score?: number;
  priority?: string;
  department_code?: string;
  ai_analysis?: VisionAnalysis;
  duplicate_of_id?: string | number;
  created_at?: string;
  updated_at?: string;
}

export interface DuplicateMatch {
  candidate_report_id: string;
  matched_issue_id: string;
  matched_issue_title: string;
  location_score: number;
  image_score: number;
  category_score: number;
  time_score: number;
  total_score: number;
  distance_meters: number;
}

export interface Department {
  id: string;
  name: string;
  slug: string;
  description?: string;
  email?: string;
  routing_categories: string[];
}

export interface Issue {
  id: string;
  title: string;
  category: string;
  description?: string;
  status: ReportStatus;
  severity: SeverityLevel;
  priority_score: number;
  priority_breakdown?: PriorityBreakdown;
  department_id?: string;
  department?: Department;
  location_id: string;
  location?: Location;
  report_count: number;
  primary_image_url?: string;
  assigned_employee_id?: string;
  assigned_employee_name?: string;
  created_at: string;
  resolved_at?: string;
}

export interface WorkOrder {
  id: string;
  issue_id: string;
  issue_title?: string;
  assigned_to_id: string;
  assigned_to_name?: string;
  assigned_by_id: string;
  priority: SeverityLevel;
  status: 'ASSIGNED' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  deadline?: string;
  notes?: string;
  before_image_url?: string;
  after_image_url?: string;
  created_at: string;
  completed_at?: string;
}

export interface AnalyticsOverview {
  total_issues: number;
  open_issues: number;
  resolved_issues: number;
  critical_issues: number;
  avg_resolution_days: number;
  community_confirmations: number;
  duplicate_reports_merged: number;
}

export interface CategoryMetric {
  category: string;
  count: number;
  percentage: number;
}

export interface ResolutionMetric {
  department_name: string;
  avg_days: number;
  resolved_count: number;
}

export interface Hotspot {
  id: string;
  area_name: string;
  issue_count: number;
  increase_pct: number;
  top_problems: string[];
  latitude: number;
  longitude: number;
  radius_km: number;
}

export interface Notification {
  id: string;
  user_id: string;
  type: string;
  title: string;
  body: string;
  data?: Record<string, any>;
  read_at?: string;
  created_at: string;
}
