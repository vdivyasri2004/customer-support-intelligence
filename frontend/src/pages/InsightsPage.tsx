import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, Tooltip, ResponsiveContainer,
} from 'recharts';
import { Brain, AlertTriangle, TrendingUp, Users, Target, ArrowLeft } from 'lucide-react';
import toast from 'react-hot-toast';
import { aiAPI, analyticsAPI } from '../services/api';
import type { AIInsight, CommonIssue } from '../types';

const COLORS = ['#3b82f6', '#22c55e', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4'];

const SEVERITY_STYLES: Record<string, string> = {
  high: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
  medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
  low: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
};

function SeverityBadge({ severity }: { severity: string }) {
  const cls = SEVERITY_STYLES[severity] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {severity}
    </span>
  );
}

function SentimentBadge({ sentiment }: { sentiment: string }) {
  const styles: Record<string, string> = {
    Positive: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
    Negative: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    Neutral: 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300',
  };
  const cls = styles[sentiment] || styles.Neutral;
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {sentiment}
    </span>
  );
}

const TABS = [
  { key: 'insights', label: 'Business Insights' },
  { key: 'issues', label: 'Common Issues' },
  { key: 'satisfaction', label: 'Satisfaction Analysis' },
] as const;

type TabKey = typeof TABS[number]['key'];

function BusinessInsightsTab({ datasetId }: { datasetId: number }) {
  const [fetched, setFetched] = useState(false);

  const { data, mutate, isPending } = useMutation({
    mutationFn: () => aiAPI.getInsights(datasetId),
    onSuccess: (data) => {
      if (!data.available) {
        toast.error(data.message || 'AI insights unavailable');
      }
      setFetched(true);
    },
    onError: () => {
      toast.error('Failed to fetch AI insights');
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Generate AI-powered business insights from your support data.
        </p>
        <button
          onClick={() => mutate()}
          disabled={isPending}
          className="flex items-center gap-2 px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors text-sm font-medium disabled:opacity-50"
        >
          <Brain className="h-4 w-4" />
          {isPending ? 'Analyzing...' : 'Fetch Insights'}
        </button>
      </div>

      {isPending && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card p-5 animate-pulse">
              <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-3" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-2" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full mb-1" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
            </div>
          ))}
        </div>
      )}

      {!isPending && fetched && data?.available === false && (
        <div className="card p-6 text-center">
          <AlertTriangle className="h-10 w-10 text-yellow-400 mx-auto mb-3" />
          <p className="text-gray-700 dark:text-gray-300 font-medium">AI Insights Unavailable</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {data.message || 'No AI provider is configured. Please check your settings.'}
          </p>
        </div>
      )}

      {!isPending && fetched && data?.available && (
        <>
          {data.summary && (
            <div className="card p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800">
              <p className="text-sm text-blue-800 dark:text-blue-300">{data.summary}</p>
            </div>
          )}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {data.insights.map((insight: AIInsight, i: number) => (
              <motion.div
                key={i}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                className="card p-5"
              >
                <div className="flex items-start justify-between mb-2">
                  <h4 className="font-semibold text-gray-900 dark:text-white">{insight.title}</h4>
                  <SeverityBadge severity={insight.severity} />
                </div>
                <span className="inline-block text-xs font-medium px-2 py-0.5 rounded-full bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300 mb-2">
                  {insight.category}
                </span>
                <p className="text-sm text-gray-600 dark:text-gray-400">{insight.description}</p>
              </motion.div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function CommonIssuesTab({ datasetId }: { datasetId: number }) {
  const { data, mutate, isPending } = useMutation({
    mutationFn: () => aiAPI.getCommonIssues(datasetId),
    onSuccess: (data) => {
      if (!data.available) {
        toast.error('AI common issues unavailable');
      }
    },
    onError: () => {
      toast.error('Failed to fetch common issues');
    },
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <p className="text-sm text-gray-500 dark:text-gray-400">
          Identify the most frequent issues reported by customers.
        </p>
        <button
          onClick={() => mutate()}
          disabled={isPending}
          className="flex items-center gap-2 px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors text-sm font-medium disabled:opacity-50"
        >
          <Brain className="h-4 w-4" />
          {isPending ? 'Analyzing...' : 'Find Common Issues'}
        </button>
      </div>

      {isPending && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 3 }).map((_, i) => (
            <div key={i} className="card p-5 animate-pulse">
              <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-2/3 mb-3" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/4 mb-2" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full" />
            </div>
          ))}
        </div>
      )}

      {!isPending && data?.available === false && (
        <div className="card p-6 text-center">
          <AlertTriangle className="h-10 w-10 text-yellow-400 mx-auto mb-3" />
          <p className="text-gray-700 dark:text-gray-300 font-medium">AI Unavailable</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            No AI provider is configured. Please check your settings.
          </p>
        </div>
      )}

      {!isPending && data?.available && data.issues && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {data.issues.map((issue: CommonIssue, i: number) => (
            <motion.div
              key={i}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05 }}
              className="card p-5"
            >
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">{issue.title}</h4>
              <div className="flex flex-wrap gap-2 mb-3">
                <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-400">
                  <TrendingUp className="h-3 w-3" />
                  {issue.frequency} tickets
                </span>
                <span className="inline-flex items-center px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-400 text-xs font-medium">
                  {issue.affected_category}
                </span>
                {issue.avg_satisfaction != null && (
                  <span className="inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded-full bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-400">
                    <Target className="h-3 w-3" />
                    {issue.avg_satisfaction.toFixed(1)}/5 satisfaction
                  </span>
                )}
                <SentimentBadge sentiment={issue.sentiment} />
              </div>
              {issue.example_tickets.length > 0 && (
                <div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Example tickets:</p>
                  <div className="flex flex-wrap gap-1">
                    {issue.example_tickets.map((tid) => (
                      <span
                        key={tid}
                        className="text-xs font-mono px-1.5 py-0.5 rounded bg-gray-100 dark:bg-gray-800 text-gray-600 dark:text-gray-400"
                      >
                        #{tid}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </motion.div>
          ))}
        </div>
      )}
    </div>
  );
}

function SatisfactionAnalysisTab({ datasetId }: { datasetId: number }) {
  const { data: analytics, isLoading } = useQuery({
    queryKey: ['analytics', datasetId],
    queryFn: () => analyticsAPI.get(datasetId),
    enabled: !!datasetId,
  });

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="card p-6 animate-pulse">
            <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-4" />
            <div className="h-64 bg-gray-200 dark:bg-gray-700 rounded" />
          </div>
        ))}
      </div>
    );
  }

  if (!analytics) return null;

  const { satisfaction_by_category, agent_performance, time_analysis } = analytics;

  const bestCategory = [...satisfaction_by_category]
    .filter((c) => c.avg_satisfaction != null)
    .sort((a, b) => (b.avg_satisfaction ?? 0) - (a.avg_satisfaction ?? 0))[0];
  const worstCategory = [...satisfaction_by_category]
    .filter((c) => c.avg_satisfaction != null)
    .sort((a, b) => (a.avg_satisfaction ?? 0) - (b.avg_satisfaction ?? 0))[0];

  const bestAgent = [...agent_performance]
    .filter((a) => a.avg_satisfaction != null)
    .sort((a, b) => (b.avg_satisfaction ?? 0) - (a.avg_satisfaction ?? 0))[0];

  const fastestCategory = [...time_analysis]
    .filter((t) => t.avg_resolution_time != null)
    .sort((a, b) => (a.avg_resolution_time ?? 0) - (b.avg_resolution_time ?? 0))[0];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {bestCategory && (
          <div className="card p-4">
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Highest Satisfaction</p>
            <p className="text-lg font-bold text-gray-900 dark:text-white mt-1">{bestCategory.category}</p>
            <p className="text-sm text-green-600 dark:text-green-400">{bestCategory.avg_satisfaction?.toFixed(1)}/5</p>
          </div>
        )}
        {worstCategory && (
          <div className="card p-4">
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Lowest Satisfaction</p>
            <p className="text-lg font-bold text-gray-900 dark:text-white mt-1">{worstCategory.category}</p>
            <p className="text-sm text-red-600 dark:text-red-400">{worstCategory.avg_satisfaction?.toFixed(1)}/5</p>
          </div>
        )}
        {bestAgent && (
          <div className="card p-4">
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Top Agent</p>
            <p className="text-lg font-bold text-gray-900 dark:text-white mt-1">{bestAgent.agent}</p>
            <p className="text-sm text-green-600 dark:text-green-400">{bestAgent.avg_satisfaction?.toFixed(1)}/5</p>
          </div>
        )}
        {fastestCategory && (
          <div className="card p-4">
            <p className="text-xs font-medium text-gray-500 dark:text-gray-400">Fastest Resolution</p>
            <p className="text-lg font-bold text-gray-900 dark:text-white mt-1">{fastestCategory.category}</p>
            <p className="text-sm text-blue-600 dark:text-blue-400">{Math.round(fastestCategory.avg_resolution_time ?? 0)} min avg</p>
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Satisfaction by Category</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={satisfaction_by_category}>
              <XAxis dataKey="category" tick={{ fontSize: 12 }} />
              <YAxis domain={[0, 5]} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="avg_satisfaction" fill="#22c55e" radius={[4, 4, 0, 0]} name="Avg Satisfaction" />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Response Time vs Satisfaction</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={time_analysis}>
              <XAxis dataKey="category" tick={{ fontSize: 12 }} />
              <YAxis tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="avg_resolution_time" fill="#f59e0b" radius={[4, 4, 0, 0]} name="Avg Resolution (min)" />
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Agent Performance Comparison</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={agent_performance}>
              <XAxis dataKey="agent" tick={{ fontSize: 12 }} />
              <YAxis domain={[0, 5]} tick={{ fontSize: 12 }} />
              <Tooltip />
              <Bar dataKey="avg_satisfaction" radius={[4, 4, 0, 0]} name="Avg Satisfaction">
                {agent_performance.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="card p-6">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Satisfaction Distribution</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={satisfaction_by_category.filter((c) => c.avg_satisfaction != null)}
                dataKey="avg_satisfaction"
                nameKey="category"
                cx="50%"
                cy="50%"
                outerRadius={100}
                label={({ name, percent }: { name: string; percent: number }) => `${name} (${(percent * 100).toFixed(0)}%)`}
              >
                {satisfaction_by_category.map((_: any, i: number) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </motion.div>
      </div>
    </div>
  );
}

export function InsightsPage() {
  const { id: datasetIdParam } = useParams<{ id: string }>();
  const datasetId = Number(datasetIdParam);
  const [activeTab, setActiveTab] = useState<TabKey>('insights');

  if (!datasetId) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <Brain className="h-16 w-16 text-gray-400 dark:text-gray-500 mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">No Dataset Selected</h2>
        <p className="text-gray-500 dark:text-gray-400 mb-6 max-w-md">
          Please select a dataset to view AI insights.
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

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Link
          to="/dashboard"
          className="flex items-center gap-1 text-sm text-brand-600 dark:text-brand-400 hover:text-brand-700 dark:hover:text-brand-300 transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Dashboard
        </Link>
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">AI Insights</h1>
      </div>

      <div className="flex gap-1 border-b border-gray-200 dark:border-gray-700">
        {TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`px-4 py-3 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === tab.key
                ? 'border-brand-600 text-brand-600 dark:text-brand-400 dark:border-brand-400'
                : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div>
        {activeTab === 'insights' && <BusinessInsightsTab datasetId={datasetId} />}
        {activeTab === 'issues' && <CommonIssuesTab datasetId={datasetId} />}
        {activeTab === 'satisfaction' && <SatisfactionAnalysisTab datasetId={datasetId} />}
      </div>
    </div>
  );
}
