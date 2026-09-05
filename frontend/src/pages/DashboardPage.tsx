import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { motion } from 'framer-motion';
import { BarChart3, Clock, ThumbsUp, Shield, AlertTriangle, TrendingUp, Save } from 'lucide-react';
import { analyticsAPI, historyAPI } from '../services/api';
import type { AnalyticsFilters } from '../types';
import toast from 'react-hot-toast';

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];

function KPICard({ icon: Icon, value, label, subtitle, color }: {
  icon: React.ElementType;
  value: string;
  label: string;
  subtitle: string;
  color: string;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card p-6"
    >
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400">{label}</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white mt-1">{value}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">{subtitle}</p>
        </div>
        <div className={`p-3 rounded-lg ${color}`}>
          <Icon className="h-6 w-6 text-white" />
        </div>
      </div>
    </motion.div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="card p-6"
    >
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">{title}</h3>
      {children}
    </motion.div>
  );
}

function SkeletonCard() {
  return (
    <div className="card p-6 animate-pulse">
      <div className="flex items-start justify-between">
        <div className="space-y-3 flex-1">
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-24" />
          <div className="h-8 bg-gray-200 dark:bg-gray-700 rounded w-20" />
          <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-32" />
        </div>
        <div className="h-12 w-12 bg-gray-200 dark:bg-gray-700 rounded-lg" />
      </div>
    </div>
  );
}

function SkeletonChart() {
  return (
    <div className="card p-6 animate-pulse">
      <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-40 mb-4" />
      <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded" />
    </div>
  );
}

export function DashboardPage() {
  const datasetId = Number(localStorage.getItem('selectedDatasetId'));

  const [filters, setFilters] = useState<AnalyticsFilters>({});

  const { data: analytics, isLoading: analyticsLoading, error: analyticsError } = useQuery({
    queryKey: ['analytics', datasetId, filters],
    queryFn: () => analyticsAPI.get(datasetId, filters),
    enabled: !!datasetId,
  });

  const { data: filterOptions } = useQuery({
    queryKey: ['filterOptions', datasetId],
    queryFn: () => analyticsAPI.getFilters(datasetId),
    enabled: !!datasetId,
  });

  const handleFilterChange = (key: keyof AnalyticsFilters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value || undefined }));
  };

  const handleSaveAnalysis = async () => {
    try {
      await historyAPI.create(datasetId, `Analysis ${new Date().toLocaleDateString()}`);
      toast.success('Analysis saved to history');
    } catch {
      toast.error('Failed to save analysis');
    }
  };

  if (!datasetId) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <BarChart3 className="h-16 w-16 text-gray-400 dark:text-gray-500 mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">No Dataset Selected</h2>
        <p className="text-gray-500 dark:text-gray-400 mb-6 max-w-md">
          Please select a dataset from the Datasets page to view analytics and insights.
        </p>
        <Link
          to="/datasets"
          className="px-6 py-3 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors font-medium"
        >
          Go to Datasets
        </Link>
      </div>
    );
  }

  if (analyticsError) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <AlertTriangle className="h-16 w-16 text-red-400 mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Error Loading Analytics</h2>
        <p className="text-gray-500 dark:text-gray-400 max-w-md">
          {(analyticsError as Error)?.message || 'An unexpected error occurred while fetching analytics data.'}
        </p>
      </div>
    );
  }

  const kpis = analytics?.kpis;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Analytics Dashboard</h1>
        <button
          onClick={handleSaveAnalysis}
          className="flex items-center gap-2 px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors text-sm font-medium"
        >
          <Save className="h-4 w-4" />
          Save Analysis
        </button>
      </div>

      <div className="card p-4">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Category</label>
            <select
              value={filters.category || ''}
              onChange={(e) => handleFilterChange('category', e.target.value)}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white"
            >
              <option value="">All</option>
              {filterOptions?.categories.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Priority</label>
            <select
              value={filters.priority || ''}
              onChange={(e) => handleFilterChange('priority', e.target.value)}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white"
            >
              <option value="">All</option>
              {filterOptions?.priorities.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Status</label>
            <select
              value={filters.status || ''}
              onChange={(e) => handleFilterChange('status', e.target.value)}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white"
            >
              <option value="">All</option>
              {filterOptions?.statuses.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Channel</label>
            <select
              value={filters.channel || ''}
              onChange={(e) => handleFilterChange('channel', e.target.value)}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white"
            >
              <option value="">All</option>
              {filterOptions?.channels.map((ch) => <option key={ch} value={ch}>{ch}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Agent</label>
            <select
              value={filters.agent || ''}
              onChange={(e) => handleFilterChange('agent', e.target.value)}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white"
            >
              <option value="">All</option>
              {filterOptions?.agents.map((a) => <option key={a} value={a}>{a}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Sentiment</label>
            <select
              value={filters.sentiment || ''}
              onChange={(e) => handleFilterChange('sentiment', e.target.value)}
              className="w-full rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white"
            >
              <option value="">All</option>
              {filterOptions?.sentiments.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>
      </div>

      {analyticsLoading ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {Array.from({ length: 4 }).map((_, i) => <SkeletonChart key={i} />)}
          </div>
        </>
      ) : analytics ? (
        <>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            <KPICard
              icon={BarChart3}
              value={kpis?.total_tickets.toLocaleString() ?? '—'}
              label="Total Tickets"
              subtitle={`Open: ${kpis?.open_tickets ?? 0} | Resolved: ${kpis?.resolved_tickets ?? 0}`}
              color="bg-blue-500"
            />
            <KPICard
              icon={Clock}
              value={kpis?.avg_response_time != null ? `${Math.round(kpis.avg_response_time)}m` : '—'}
              label="Avg Response Time"
              subtitle="minutes to first response"
              color="bg-amber-500"
            />
            <KPICard
              icon={Clock}
              value={kpis?.avg_resolution_time != null ? `${Math.round(kpis.avg_resolution_time)}m` : '—'}
              label="Avg Resolution Time"
              subtitle="minutes to resolution"
              color="bg-orange-500"
            />
            <KPICard
              icon={ThumbsUp}
              value={kpis?.avg_satisfaction != null ? `${kpis.avg_satisfaction.toFixed(1)}/5` : '—'}
              label="Customer Satisfaction"
              subtitle="average score out of 5"
              color="bg-green-500"
            />
            <KPICard
              icon={Shield}
              value={kpis?.sla_compliance != null ? `${kpis.sla_compliance.toFixed(1)}%` : '—'}
              label="SLA Compliance"
              subtitle="tickets meeting SLA"
              color="bg-indigo-500"
            />
            <KPICard
              icon={TrendingUp}
              value={kpis?.negative_sentiment_pct != null ? `${kpis.negative_sentiment_pct.toFixed(1)}%` : '—'}
              label="Negative Sentiment"
              subtitle="percentage of negative tickets"
              color="bg-red-500"
            />
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ChartCard title="Tickets Over Time">
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={analytics.tickets_over_time}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} dot={false} name="Tickets" />
                </LineChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Tickets by Category">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analytics.tickets_by_category}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="category" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Count" />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Tickets by Status">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={analytics.tickets_by_status}
                    dataKey="count"
                    nameKey="status"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={({ name, percent }: { name: string; percent: number }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                  >
                    {analytics.tickets_by_status.map((_: any, i: number) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Tickets by Priority">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={analytics.tickets_by_priority}
                    dataKey="count"
                    nameKey="priority"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={({ name, percent }: { name: string; percent: number }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                  >
                    {analytics.tickets_by_priority.map((_: any, i: number) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Sentiment Distribution">
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={analytics.sentiment_distribution}
                    dataKey="count"
                    nameKey="sentiment"
                    cx="50%"
                    cy="50%"
                    outerRadius={100}
                    label={({ name, percent }: { name: string; percent: number }) => `${name} (${(percent * 100).toFixed(0)}%)`}
                  >
                    {analytics.sentiment_distribution.map((_: any, i: number) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Satisfaction by Category">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analytics.satisfaction_by_category}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="category" tick={{ fontSize: 12 }} />
                  <YAxis domain={[0, 5]} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="avg_satisfaction" fill="#22c55e" radius={[4, 4, 0, 0]} name="Avg Satisfaction" />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Agent Performance">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analytics.agent_performance}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="agent" tick={{ fontSize: 12 }} />
                  <YAxis domain={[0, 5]} tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="avg_satisfaction" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Avg Satisfaction" />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>

            <ChartCard title="Time Analysis by Category">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={analytics.time_analysis}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="category" tick={{ fontSize: 12 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip />
                  <Legend />
                  <Bar dataKey="avg_response_time" fill="#f59e0b" radius={[4, 4, 0, 0]} name="Avg Response (min)" />
                  <Bar dataKey="avg_resolution_time" fill="#ef4444" radius={[4, 4, 0, 0]} name="Avg Resolution (min)" />
                </BarChart>
              </ResponsiveContainer>
            </ChartCard>
          </div>
        </>
      ) : null}
    </div>
  );
}
