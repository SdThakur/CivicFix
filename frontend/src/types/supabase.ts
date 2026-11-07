export type Json =
  | string
  | number
  | boolean
  | null
  | { [key: string]: Json | undefined }
  | Json[];

export type Database = {
  public: {
    Tables: {
      profiles: {
        Row: {
          id: string;
          email: string | null;
          full_name: string | null;
          phone: string | null;
          role: 'CITIZEN' | 'STAFF' | 'MANAGER' | 'DISPATCHER' | 'INSPECTOR' | 'FIELD_WORKER' | 'ADMIN';
          avatar_url: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id: string;
          email?: string | null;
          full_name?: string | null;
          phone?: string | null;
          role?: 'CITIZEN' | 'STAFF' | 'MANAGER' | 'DISPATCHER' | 'INSPECTOR' | 'FIELD_WORKER' | 'ADMIN';
          avatar_url?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          email?: string | null;
          full_name?: string | null;
          phone?: string | null;
          role?: 'CITIZEN' | 'STAFF' | 'MANAGER' | 'DISPATCHER' | 'INSPECTOR' | 'FIELD_WORKER' | 'ADMIN';
          avatar_url?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [];
      };
      issues: {
        Row: {
          id: string;
          tracking_number: string;
          title: string;
          category: string;
          description: string | null;
          status: 'SUBMITTED' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED' | 'CANCELLED';
          priority_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
          priority_score: number;
          score_factors: Json;
          lat: number;
          lng: number;
          address: string | null;
          neighborhood: string | null;
          department_code: string | null;
          upvotes: number;
          duplicate_count: number;
          before_photo_path: string | null;
          after_photo_path: string | null;
          created_at: string;
          updated_at: string;
          resolved_at: string | null;
        };
        Insert: {
          id?: string;
          tracking_number: string;
          title: string;
          category: string;
          description?: string | null;
          status?: 'SUBMITTED' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED' | 'CANCELLED';
          priority_level?: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
          priority_score?: number;
          score_factors?: Json;
          lat: number;
          lng: number;
          address?: string | null;
          neighborhood?: string | null;
          department_code?: string | null;
          upvotes?: number;
          duplicate_count?: number;
          before_photo_path?: string | null;
          after_photo_path?: string | null;
          created_at?: string;
          updated_at?: string;
          resolved_at?: string | null;
        };
        Update: {
          id?: string;
          tracking_number?: string;
          title?: string;
          category?: string;
          description?: string | null;
          status?: 'SUBMITTED' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED' | 'CANCELLED';
          priority_level?: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
          priority_score?: number;
          score_factors?: Json;
          lat?: number;
          lng?: number;
          address?: string | null;
          neighborhood?: string | null;
          department_code?: string | null;
          upvotes?: number;
          duplicate_count?: number;
          before_photo_path?: string | null;
          after_photo_path?: string | null;
          created_at?: string;
          updated_at?: string;
          resolved_at?: string | null;
        };
        Relationships: [];
      };
      reports: {
        Row: {
          id: string;
          user_id: string;
          issue_id: string | null;
          image_path: string;
          lat: number;
          lng: number;
          description: string | null;
          category: string | null;
          ai_confidence: number | null;
          status: 'PENDING' | 'PROCESSING' | 'DONE' | 'FAILED' | 'DUPLICATE';
          error_message: string | null;
          is_duplicate: boolean;
          duplicate_of_id: string | null;
          created_at: string;
          updated_at: string;
        };
        Insert: {
          id?: string;
          user_id: string;
          issue_id?: string | null;
          image_path: string;
          lat: number;
          lng: number;
          description?: string | null;
          category?: string | null;
          ai_confidence?: number | null;
          status?: 'PENDING' | 'PROCESSING' | 'DONE' | 'FAILED' | 'DUPLICATE';
          error_message?: string | null;
          is_duplicate?: boolean;
          duplicate_of_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Update: {
          id?: string;
          user_id?: string;
          issue_id?: string | null;
          image_path?: string;
          lat?: number;
          lng?: number;
          description?: string | null;
          category?: string | null;
          ai_confidence?: number | null;
          status?: 'PENDING' | 'PROCESSING' | 'DONE' | 'FAILED' | 'DUPLICATE';
          error_message?: string | null;
          is_duplicate?: boolean;
          duplicate_of_id?: string | null;
          created_at?: string;
          updated_at?: string;
        };
        Relationships: [];
      };
      issue_timeline: {
        Row: {
          id: string;
          issue_id: string;
          status: string;
          message: string;
          actor_id: string | null;
          metadata: Json | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          issue_id: string;
          status: string;
          message: string;
          actor_id?: string | null;
          metadata?: Json | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          issue_id?: string;
          status?: string;
          message?: string;
          actor_id?: string | null;
          metadata?: Json | null;
          created_at?: string;
        };
        Relationships: [];
      };
      issue_upvotes: {
        Row: {
          user_id: string;
          issue_id: string;
          created_at: string;
        };
        Insert: {
          user_id: string;
          issue_id: string;
          created_at?: string;
        };
        Update: {
          user_id?: string;
          issue_id?: string;
          created_at?: string;
        };
        Relationships: [];
      };
      audit_log: {
        Row: {
          id: string;
          entity_name: string;
          entity_id: string;
          action: string;
          old_data: Json | null;
          new_data: Json | null;
          performed_by: string | null;
          created_at: string;
        };
        Insert: {
          id?: string;
          entity_name: string;
          entity_id: string;
          action: string;
          old_data?: Json | null;
          new_data?: Json | null;
          performed_by?: string | null;
          created_at?: string;
        };
        Update: {
          id?: string;
          entity_name?: string;
          entity_id?: string;
          action?: string;
          old_data?: Json | null;
          new_data?: Json | null;
          performed_by?: string | null;
          created_at?: string;
        };
        Relationships: [];
      };
    };
    Views: {
      public_issues: {
        Row: {
          id: string;
          tracking_number: string;
          title: string;
          category: string;
          description: string | null;
          status: 'SUBMITTED' | 'IN_PROGRESS' | 'RESOLVED' | 'CLOSED' | 'CANCELLED';
          priority_level: 'LOW' | 'MEDIUM' | 'HIGH' | 'URGENT';
          priority_score: number;
          score_factors: Json;
          lat: number;
          lng: number;
          address: string | null;
          neighborhood: string | null;
          department_code: string | null;
          upvotes: number;
          duplicate_count: number;
          before_photo_path: string | null;
          after_photo_path: string | null;
          created_at: string;
          updated_at: string;
          resolved_at: string | null;
        };
      };
      public_issue_timeline: {
        Row: {
          id: string;
          issue_id: string;
          status: string;
          message: string;
          created_at: string;
        };
      };
      public_proofs: {
        Row: {
          issue_id: string;
          tracking_number: string;
          before_photo_path: string | null;
          after_photo_path: string | null;
          resolved_at: string | null;
        };
      };
      public_stats: {
        Row: {
          total_issues: number;
          resolved_issues: number;
          in_progress_issues: number;
          open_issues: number;
          resolution_rate_pct: number;
          avg_resolution_hours: number;
          refreshed_at: string;
        };
      };
      public_category_stats: {
        Row: {
          category: string;
          total_count: number;
          resolved_count: number;
          avg_priority: number;
          avg_turnaround_hours: number;
          refreshed_at: string;
        };
      };
    };
    Functions: {
      issues_in_bounds: {
        Args: {
          min_lat: number;
          max_lat: number;
          min_lng: number;
          max_lng: number;
          category_filter?: string | null;
          status_filter?: string | null;
          p_limit?: number;
        };
        Returns: {
          id: string;
          tracking_number: string;
          title: string;
          category: string;
          status: string;
          priority_level: string;
          priority_score: number;
          lat: number;
          lng: number;
          address: string | null;
          neighborhood: string | null;
          upvotes: number;
          duplicate_count: number;
          created_at: string;
          resolved_at: string | null;
        }[];
      };
      nearby_issues: {
        Args: {
          user_lat: number;
          user_lng: number;
          radius_meters?: number;
          p_limit?: number;
        };
        Returns: {
          id: string;
          tracking_number: string;
          title: string;
          category: string;
          status: string;
          distance_meters: number;
          upvotes: number;
          duplicate_count: number;
          created_at: string;
        }[];
      };
    };
  };
};

