import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { History, Trash2, ExternalLink, BarChart3, ThumbsUp, Shield, Clock } from 'lucide-react';
import toast from 'react-hot-toast';
import { historyAPI } from '../services/api';
import type { Analysis } from '../types';

function formatDate(dateStr: string) {
  return new Date(dateStr).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function MetricPill({ icon: Icon, label, value }: {
  icon: React.ElementType;
  label: string;
  value: string;
}) {
  return (
    <div className="flex items-center gap-1.5 text-xs text-gray-500 dark:text-gray-400">
      <Icon className="h-3.5 w-3.5" />
      <span>{label}:</span>
      <span className="font-medium text-gray-700 dark:text-gray-300">{value}</span>
    </div>
  );
}

export function HistoryPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['analyses'],
    queryFn: () => historyAPI.list(),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => historyAPI.delete(id),
    onSuccess: () => {
      toast.success('Analysis deleted');
      queryClient.invalidateQueries({ queryKey: ['analyses'] });
    },
    onError: () => {
      toast.error('Failed to delete analysis');
    },
  });

  const handleDelete = (id: number, name: string) => {
    if (window.confirm(`Delete analysis "${name}"?`)) {
      deleteMutation.mutate(id);
    }
  };

  const handleOpen = (analysis: Analysis) => {
    localStorage.setItem('selectedDatasetId', String(analysis.dataset_id));
    navigate('/dashboard');
  };

  const getMetrics = (analysis: Analysis) => {
    const summary = analysis.summary_json as Record<string, unknown> | null;
    if (!summary) return null;
    return {
      totalTickets: summary.total_tickets as number | undefined,
      satisfaction: summary.avg_satisfaction as number | undefined,
      slaCompliance: summary.sla_compliance as number | undefined,
    };
  };

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Analysis History</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <div key={i} className="card p-5 animate-pulse">
              <div className="h-5 bg-gray-200 dark:bg-gray-700 rounded w-1/3 mb-3" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2 mb-2" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-2/3" />
            </div>
          ))}
        </div>
      </div>
    );
  }

  const analyses = data?.analyses ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Analysis History</h1>
        {analyses.length > 0 && (
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {analyses.length} saved {analyses.length === 1 ? 'analysis' : 'analyses'}
          </p>
        )}
      </div>

      {analyses.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <History className="h-16 w-16 text-gray-400 dark:text-gray-500 mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">No Saved Analyses</h3>
          <p className="text-sm text-gray-500 dark:text-gray-400 max-w-md mb-6">
            Save an analysis from the dashboard to see it here. Your saved analyses will include key metrics and can be reopened anytime.
          </p>
          <button
            onClick={() => navigate('/datasets')}
            className="px-5 py-2.5 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors text-sm font-medium"
          >
            Browse Datasets
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {analyses.map((analysis: Analysis) => {
            const metrics = getMetrics(analysis);
            return (
              <motion.div
                key={analysis.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="card p-5"
              >
                <div className="flex items-start justify-between mb-3">
                  <div className="min-w-0">
                    <h3 className="font-semibold text-gray-900 dark:text-white truncate">
                      {analysis.analysis_name}
                    </h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Dataset #{analysis.dataset_id}
                    </p>
                  </div>
                  <span className="text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap ml-3">
                    {formatDate(analysis.created_at)}
                  </span>
                </div>

                {metrics && (
                  <div className="flex flex-wrap gap-3 mb-4">
                    {metrics.totalTickets != null && (
                      <MetricPill icon={BarChart3} label="Tickets" value={metrics.totalTickets.toLocaleString()} />
                    )}
                    {metrics.satisfaction != null && (
                      <MetricPill icon={ThumbsUp} label="Satisfaction" value={`${metrics.satisfaction.toFixed(1)}/5`} />
                    )}
                    {metrics.slaCompliance != null && (
                      <MetricPill icon={Shield} label="SLA" value={`${metrics.slaCompliance.toFixed(1)}%`} />
                    )}
                  </div>
                )}

                <div className="flex gap-2">
                  <button
                    onClick={() => handleOpen(analysis)}
                    className="flex items-center gap-1.5 px-3 py-1.5 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors text-xs font-medium"
                  >
                    <ExternalLink className="h-3.5 w-3.5" />
                    Open
                  </button>
                  <button
                    onClick={() => handleDelete(analysis.id, analysis.analysis_name)}
                    disabled={deleteMutation.isPending}
                    className="flex items-center gap-1.5 px-3 py-1.5 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors text-xs font-medium disabled:opacity-50"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    Delete
                  </button>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </div>
  );
}
