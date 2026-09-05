import { useState } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { useParams, Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Search, ChevronLeft, ChevronRight, X, ExternalLink, Brain } from 'lucide-react';
import toast from 'react-hot-toast';
import { ticketsAPI, aiAPI, analyticsAPI } from '../services/api';
import type { Ticket } from '../types';

const PAGE_SIZE = 20;

function SentimentBadge({ sentiment }: { sentiment: string | null }) {
  if (!sentiment) return <span className="text-gray-400">—</span>;
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

function PriorityBadge({ priority }: { priority: string | null }) {
  if (!priority) return <span className="text-gray-400">—</span>;
  const styles: Record<string, string> = {
    Critical: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400',
    High: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-400',
    Medium: 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400',
    Low: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400',
  };
  const cls = styles[priority] || 'bg-gray-100 text-gray-800 dark:bg-gray-700 dark:text-gray-300';
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {priority}
    </span>
  );
}

function SkeletonTable({ rows = 10 }: { rows?: number }) {
  return (
    <div className="card overflow-hidden">
      <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
        <thead className="bg-gray-50 dark:bg-gray-800">
          <tr>
            {['ID', 'Subject', 'Category', 'Priority', 'Status', 'Agent', 'Sentiment', 'Satisfaction', 'Response'].map((h) => (
              <th key={h} className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">{h}</th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
          {Array.from({ length: rows }).map((_, i) => (
            <tr key={i}>
              {Array.from({ length: 9 }).map((_, j) => (
                <td key={j} className="px-4 py-3">
                  <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded animate-pulse" style={{ width: `${50 + (j % 3) * 20}%` }} />
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="flex flex-col items-center justify-center py-20 text-center">
      <Search className="h-12 w-12 text-gray-400 dark:text-gray-500 mb-4" />
      <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-1">No tickets found</h3>
      <p className="text-sm text-gray-500 dark:text-gray-400">Try adjusting your search or filters.</p>
    </div>
  );
}

function TicketDetailPanel({
  ticket,
  onClose,
}: {
  ticket: Ticket;
  onClose: () => void;
}) {
  const [summary, setSummary] = useState<string | null>(ticket.ai_summary);
  const [summaryUnavailable, setSummaryUnavailable] = useState(false);

  const summarizeMutation = useMutation({
    mutationFn: () => aiAPI.summarizeTicket(ticket.id),
    onSuccess: (data) => {
      if (data.available && data.summary) {
        setSummary(data.summary);
        setSummaryUnavailable(false);
      } else {
        setSummary(null);
        setSummaryUnavailable(true);
        toast.error(data.message || 'AI summary unavailable');
      }
    },
    onError: () => {
      toast.error('Failed to generate AI summary');
    },
  });

  const formatDate = (v: string | null) => (v ? new Date(v).toLocaleString() : '—');
  const formatMinutes = (v: number | null) => (v != null ? `${Math.round(v)} min` : '—');

  return (
    <motion.div
      initial={{ x: '100%' }}
      animate={{ x: 0 }}
      exit={{ x: '100%' }}
      transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      className="fixed inset-y-0 right-0 w-full max-w-xl bg-white dark:bg-gray-900 shadow-2xl z-50 flex flex-col border-l border-gray-200 dark:border-gray-700"
    >
      <div className="flex items-center justify-between px-6 py-4 border-b border-gray-200 dark:border-gray-700">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white truncate pr-4">
          {ticket.subject || `Ticket #${ticket.id}`}
        </h2>
        <button onClick={onClose} className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors">
          <X className="h-5 w-5 text-gray-500" />
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-6 space-y-6">
        <div className="space-y-4">
          <div>
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Description</h3>
            <p className="text-sm text-gray-900 dark:text-white whitespace-pre-wrap">
              {ticket.description || 'No description'}
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <h3 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Category</h3>
              <p className="text-sm text-gray-900 dark:text-white">{ticket.category || '—'}</p>
            </div>
            <div>
              <h3 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Priority</h3>
              <PriorityBadge priority={ticket.priority} />
            </div>
            <div>
              <h3 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Status</h3>
              <p className="text-sm text-gray-900 dark:text-white">{ticket.status || '—'}</p>
            </div>
            <div>
              <h3 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Agent</h3>
              <p className="text-sm text-gray-900 dark:text-white">{ticket.agent || '—'}</p>
            </div>
            <div>
              <h3 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Channel</h3>
              <p className="text-sm text-gray-900 dark:text-white">{ticket.channel || '—'}</p>
            </div>
            <div>
              <h3 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Sentiment</h3>
              <SentimentBadge sentiment={ticket.sentiment} />
            </div>
          </div>
        </div>

        <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
          <h3 className="text-sm font-semibold text-gray-900 dark:text-white mb-3">Timeline</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Created At</h4>
              <p className="text-sm text-gray-900 dark:text-white">{formatDate(ticket.created_at)}</p>
            </div>
            <div>
              <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">First Response At</h4>
              <p className="text-sm text-gray-900 dark:text-white">{formatDate(ticket.first_response_at)}</p>
            </div>
            <div>
              <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Resolved At</h4>
              <p className="text-sm text-gray-900 dark:text-white">{formatDate(ticket.resolved_at)}</p>
            </div>
            <div>
              <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Response Time</h4>
              <p className="text-sm text-gray-900 dark:text-white">{formatMinutes(ticket.response_time_minutes)}</p>
            </div>
            <div>
              <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Resolution Time</h4>
              <p className="text-sm text-gray-900 dark:text-white">{formatMinutes(ticket.resolution_time_minutes)}</p>
            </div>
            <div>
              <h4 className="text-xs font-medium text-gray-500 dark:text-gray-400 mb-1">Satisfaction Score</h4>
              <p className="text-sm text-gray-900 dark:text-white">
                {ticket.satisfaction_score != null ? `${ticket.satisfaction_score} / 5` : '—'}
              </p>
            </div>
          </div>
        </div>

        <div className="border-t border-gray-200 dark:border-gray-700 pt-4">
          <div className="flex items-center justify-between mb-3">
            <h3 className="text-sm font-semibold text-gray-900 dark:text-white flex items-center gap-2">
              <Brain className="h-4 w-4" />
              AI Summary
            </h3>
            <button
              onClick={() => summarizeMutation.mutate()}
              disabled={summarizeMutation.isPending}
              className="flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-900/20 rounded-lg hover:bg-brand-100 dark:hover:bg-brand-900/40 transition-colors disabled:opacity-50"
            >
              <Brain className="h-3.5 w-3.5" />
              {summarizeMutation.isPending ? 'Generating...' : 'Generate Summary'}
            </button>
          </div>

          {summarizeMutation.isPending && (
            <div className="space-y-2 animate-pulse">
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/4" />
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-1/2" />
            </div>
          )}

          {!summarizeMutation.isPending && summary && (
            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap leading-relaxed">
              {summary}
            </p>
          )}

          {!summarizeMutation.isPending && !summary && summaryUnavailable && (
            <p className="text-sm text-gray-500 dark:text-gray-400 italic">
              AI summary is currently unavailable for this ticket.
            </p>
          )}
        </div>
      </div>
    </motion.div>
  );
}

export function TicketsPage() {
  const { datasetId: datasetIdParam } = useParams<{ datasetId: string }>();
  const datasetId = Number(datasetIdParam);

  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState('created_at');
  const [sortDir, setSortDir] = useState<'desc' | 'asc'>('desc');
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null);

  const [filterCategory, setFilterCategory] = useState('');
  const [filterPriority, setFilterPriority] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [filterChannel, setFilterChannel] = useState('');
  const [filterAgent, setFilterAgent] = useState('');
  const [filterSentiment, setFilterSentiment] = useState('');

  const { data: filterOptions } = useQuery({
    queryKey: ['filterOptions', datasetId],
    queryFn: () => analyticsAPI.getFilters(datasetId),
    enabled: !!datasetId,
  });

  const params: Record<string, string | number> = {
    page,
    page_size: PAGE_SIZE,
    sort_by: sortBy,
    sort_dir: sortDir,
  };
  if (search) params.search = search;
  if (filterCategory) params.category = filterCategory;
  if (filterPriority) params.priority = filterPriority;
  if (filterStatus) params.status = filterStatus;
  if (filterChannel) params.channel = filterChannel;
  if (filterAgent) params.agent = filterAgent;
  if (filterSentiment) params.sentiment = filterSentiment;

  const { data, isLoading, error } = useQuery({
    queryKey: ['tickets', datasetId, params],
    queryFn: () => ticketsAPI.list(datasetId, params),
    enabled: !!datasetId,
  });

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 0;

  const handleSort = (col: string) => {
    if (sortBy === col) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortBy(col);
      setSortDir('desc');
    }
    setPage(1);
  };

  const applySearch = () => {
    setPage(1);
  };

  if (!datasetId) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">No Dataset Selected</h2>
        <p className="text-gray-500 dark:text-gray-400 mb-6">Please select a dataset to view tickets.</p>
        <Link to="/datasets" className="px-6 py-3 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors font-medium">
          Go to Datasets
        </Link>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Error Loading Tickets</h2>
        <p className="text-gray-500 dark:text-gray-400">
          {(error as Error)?.message || 'An unexpected error occurred.'}
        </p>
      </div>
    );
  }

  const SortIndicator = ({ col }: { col: string }) => {
    if (sortBy !== col) return null;
    return <span className="ml-1 text-brand-500">{sortDir === 'asc' ? '↑' : '↓'}</span>;
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Ticket Explorer</h1>
          <Link
            to="/dashboard"
            className="flex items-center gap-1 text-sm text-brand-600 dark:text-brand-400 hover:text-brand-700 dark:hover:text-brand-300 transition-colors"
          >
            <ExternalLink className="h-4 w-4" />
            Back to Dashboard
          </Link>
        </div>
        {data && (
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {data.total.toLocaleString()} tickets
          </p>
        )}
      </div>

      <div className="card p-4">
        <div className="flex flex-col gap-4">
          <div className="flex items-center gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
              <input
                type="text"
                placeholder="Search tickets..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && applySearch()}
                className="w-full pl-10 pr-4 py-2 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
              />
            </div>
            <button
              onClick={applySearch}
              className="px-4 py-2 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors text-sm font-medium"
            >
              Search
            </button>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-7 gap-3">
            <select
              value={sortBy}
              onChange={(e) => { setSortBy(e.target.value); setPage(1); }}
              className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white"
            >
              <option value="created_at">Sort: Created At</option>
              <option value="priority">Sort: Priority</option>
              <option value="status">Sort: Status</option>
              <option value="satisfaction_score">Sort: Satisfaction</option>
            </select>
            <select
              value={sortDir}
              onChange={(e) => { setSortDir(e.target.value as 'asc' | 'desc'); setPage(1); }}
              className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white"
            >
              <option value="desc">Descending</option>
              <option value="asc">Ascending</option>
            </select>
            <select value={filterCategory} onChange={(e) => { setFilterCategory(e.target.value); setPage(1); }}
              className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white">
              <option value="">Category: All</option>
              {filterOptions?.categories.map((c) => <option key={c} value={c}>{c}</option>)}
            </select>
            <select value={filterPriority} onChange={(e) => { setFilterPriority(e.target.value); setPage(1); }}
              className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white">
              <option value="">Priority: All</option>
              {filterOptions?.priorities.map((p) => <option key={p} value={p}>{p}</option>)}
            </select>
            <select value={filterStatus} onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }}
              className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white">
              <option value="">Status: All</option>
              {filterOptions?.statuses.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
            <select value={filterChannel} onChange={(e) => { setFilterChannel(e.target.value); setPage(1); }}
              className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white">
              <option value="">Channel: All</option>
              {filterOptions?.channels.map((ch) => <option key={ch} value={ch}>{ch}</option>)}
            </select>
            <select value={filterSentiment} onChange={(e) => { setFilterSentiment(e.target.value); setPage(1); }}
              className="rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-white">
              <option value="">Sentiment: All</option>
              {filterOptions?.sentiments.map((s) => <option key={s} value={s}>{s}</option>)}
            </select>
          </div>
        </div>
      </div>

      {isLoading ? (
        <SkeletonTable />
      ) : data && data.tickets.length === 0 ? (
        <div className="card">
          <EmptyState />
        </div>
      ) : data ? (
        <div className="card overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                {[
                  { key: 'id', label: 'Ticket ID' },
                  { key: 'subject', label: 'Subject' },
                  { key: 'category', label: 'Category' },
                  { key: 'priority', label: 'Priority' },
                  { key: 'status', label: 'Status' },
                  { key: 'agent', label: 'Agent' },
                  { key: 'sentiment', label: 'Sentiment' },
                  { key: 'satisfaction_score', label: 'Satisfaction' },
                  { key: 'response_time_minutes', label: 'Response Time' },
                ].map(({ key, label }) => (
                  <th
                    key={key}
                    className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider cursor-pointer select-none hover:text-gray-700 dark:hover:text-gray-200"
                    onClick={() => handleSort(key)}
                  >
                    {label}
                    <SortIndicator col={key} />
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {data.tickets.map((ticket) => (
                <tr
                  key={ticket.id}
                  onClick={() => setSelectedTicket(ticket)}
                  className="cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors"
                >
                  <td className="px-4 py-3 text-sm text-gray-900 dark:text-white font-mono">
                    {ticket.external_ticket_id || ticket.id}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900 dark:text-white max-w-[250px] truncate">
                    {ticket.subject || '—'}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">
                    {ticket.category || '—'}
                  </td>
                  <td className="px-4 py-3">
                    <PriorityBadge priority={ticket.priority} />
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">
                    {ticket.status || '—'}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">
                    {ticket.agent || '—'}
                  </td>
                  <td className="px-4 py-3">
                    <SentimentBadge sentiment={ticket.sentiment} />
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">
                    {ticket.satisfaction_score != null ? `${ticket.satisfaction_score}/5` : '—'}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-300">
                    {ticket.response_time_minutes != null ? `${Math.round(ticket.response_time_minutes)}m` : '—'}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}

      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            Page {page} of {totalPages}
          </p>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
              className="flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <ChevronLeft className="h-4 w-4" />
              Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
              className="flex items-center gap-1 px-3 py-2 text-sm font-medium rounded-lg border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              Next
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      <AnimatePresence>
        {selectedTicket && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.3 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black z-40"
              onClick={() => setSelectedTicket(null)}
            />
            <TicketDetailPanel
              ticket={selectedTicket}
              onClose={() => setSelectedTicket(null)}
            />
          </>
        )}
      </AnimatePresence>
    </div>
  );
}
