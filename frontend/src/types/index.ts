export interface User {
  id: number;
  email: string;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Dataset {
  id: number;
  name: string;
  source_type: string;
  original_filename: string | null;
  row_count: number;
  created_at: string;
  updated_at: string;
}

export interface Ticket {
  id: number;
  dataset_id: number;
  external_ticket_id: string | null;
  customer_id: string | null;
  created_at: string | null;
  updated_at: string | null;
  category: string | null;
  subcategory: string | null;
  priority: string | null;
  status: string | null;
  subject: string | null;
  description: string | null;
  channel: string | null;
  agent: string | null;
  first_response_at: string | null;
  resolved_at: string | null;
  response_time_minutes: number | null;
  resolution_time_minutes: number | null;
  satisfaction_score: number | null;
  sentiment: string | null;
  sentiment_score: number | null;
  sla_met: boolean | null;
  ai_summary: string | null;
}

export interface KPIMetrics {
  total_tickets: number;
  open_tickets: number;
  resolved_tickets: number;
  closed_tickets: number;
  avg_response_time: number | null;
  avg_resolution_time: number | null;
  avg_satisfaction: number | null;
  sla_compliance: number | null;
  high_priority_pct: number | null;
  negative_sentiment_pct: number | null;
}

export interface TrendData {
  date: string;
  count: number;
}

export interface CategoryData {
  category: string;
  count: number;
}

export interface StatusData {
  status: string;
  count: number;
}

export interface PriorityData {
  priority: string;
  count: number;
}

export interface ChannelData {
  channel: string;
  count: number;
}

export interface SentimentData {
  sentiment: string;
  count: number;
}

export interface SatisfactionByCategory {
  category: string;
  avg_satisfaction: number | null;
  count: number;
}

export interface AgentData {
  agent: string;
  total: number;
  resolved: number;
  avg_satisfaction: number | null;
  avg_response_time: number | null;
  avg_resolution_time: number | null;
}

export interface TimeAnalysis {
  category: string;
  avg_response_time: number | null;
  avg_resolution_time: number | null;
  count: number;
}

export interface AnalyticsResponse {
  kpis: KPIMetrics;
  tickets_over_time: TrendData[];
  tickets_by_category: CategoryData[];
  tickets_by_status: StatusData[];
  tickets_by_priority: PriorityData[];
  tickets_by_channel: ChannelData[];
  sentiment_distribution: SentimentData[];
  satisfaction_by_category: SatisfactionByCategory[];
  agent_performance: AgentData[];
  time_analysis: TimeAnalysis[];
}

export interface AnalyticsFilters {
  date_from?: string;
  date_to?: string;
  category?: string;
  priority?: string;
  status?: string;
  channel?: string;
  agent?: string;
  sentiment?: string;
}

export interface FilterOptions {
  categories: string[];
  priorities: string[];
  statuses: string[];
  channels: string[];
  agents: string[];
  sentiments: string[];
  date_min: string | null;
  date_max: string | null;
}

export interface AIInsight {
  title: string;
  description: string;
  category: string;
  severity: string;
}

export interface CommonIssue {
  title: string;
  frequency: number;
  affected_category: string;
  avg_satisfaction: number | null;
  sentiment: string;
  example_tickets: number[];
}

export interface Analysis {
  id: number;
  user_id: number;
  dataset_id: number;
  analysis_name: string;
  summary_json: Record<string, unknown> | null;
  created_at: string;
  updated_at: string;
}
