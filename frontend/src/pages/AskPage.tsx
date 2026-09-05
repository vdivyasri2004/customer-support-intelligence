import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useMutation } from '@tanstack/react-query';
import { motion } from 'framer-motion';
import { Brain, ArrowLeft, Send, AlertTriangle, Sparkles } from 'lucide-react';
import toast from 'react-hot-toast';
import { aiAPI } from '../services/api';

const SUGGESTED_QUESTIONS = [
  'What are the most common customer complaints?',
  'Which category has the lowest satisfaction?',
  'Which agents have the longest resolution times?',
  'What should the support team improve?',
  'Which issues are increasing?',
];

function FactsDisplay({ facts }: { facts: Record<string, unknown> }) {
  const entries = Object.entries(facts);
  if (entries.length === 0) return null;

  return (
    <div className="card p-4 bg-gray-50 dark:bg-gray-800/50">
      <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3 flex items-center gap-2">
        <Sparkles className="h-4 w-4" />
        Calculated Facts
      </h4>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
        {entries.map(([key, value]) => (
          <div
            key={key}
            className="flex items-baseline justify-between px-3 py-2 rounded-lg bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700"
          >
            <span className="text-xs text-gray-500 dark:text-gray-400 mr-2">{key}</span>
            <span className="text-sm font-medium text-gray-900 dark:text-white text-right">
              {typeof value === 'number' ? value.toLocaleString() : String(value)}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function AskPage() {
  const { id: datasetIdParam } = useParams<{ id: string }>();
  const datasetId = Number(datasetIdParam);
  const [question, setQuestion] = useState('');

  const { data, mutate, isPending } = useMutation({
    mutationFn: (q: string) => aiAPI.askQuestion(datasetId, q),
    onError: () => {
      toast.error('Failed to get answer');
    },
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim()) return;
    mutate(question.trim());
  };

  const handleSuggested = (q: string) => {
    setQuestion(q);
    mutate(q);
  };

  if (!datasetId) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] text-center">
        <Brain className="h-16 w-16 text-gray-400 dark:text-gray-500 mb-4" />
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">No Dataset Selected</h2>
        <p className="text-gray-500 dark:text-gray-400 mb-6 max-w-md">
          Please select a dataset to ask questions.
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
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">Ask Intelligence</h1>
      </div>

      <form onSubmit={handleSubmit} className="card p-4">
        <div className="flex gap-3">
          <input
            type="text"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            placeholder="Ask a question about your support data..."
            className="flex-1 px-4 py-2.5 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-sm text-gray-900 dark:text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
          />
          <button
            type="submit"
            disabled={isPending || !question.trim()}
            className="flex items-center gap-2 px-5 py-2.5 bg-brand-600 text-white rounded-lg hover:bg-brand-700 transition-colors text-sm font-medium disabled:opacity-50"
          >
            <Send className="h-4 w-4" />
            {isPending ? 'Thinking...' : 'Ask'}
          </button>
        </div>
      </form>

      <div className="flex flex-wrap gap-2">
        {SUGGESTED_QUESTIONS.map((q) => (
          <button
            key={q}
            onClick={() => handleSuggested(q)}
            disabled={isPending}
            className="px-3 py-1.5 text-xs font-medium rounded-full border border-gray-300 dark:border-gray-600 text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white transition-colors disabled:opacity-50"
          >
            {q}
          </button>
        ))}
      </div>

      {isPending && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="card p-6">
          <div className="flex items-center gap-3 mb-4">
            <Brain className="h-5 w-5 text-brand-500 animate-pulse" />
            <span className="text-sm text-gray-500 dark:text-gray-400">Analyzing your question...</span>
          </div>
          <div className="space-y-2 animate-pulse">
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-full" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-4/5" />
            <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded w-3/5" />
          </div>
        </motion.div>
      )}

      {!isPending && data?.available === false && (
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="card p-6 text-center">
          <AlertTriangle className="h-10 w-10 text-yellow-400 mx-auto mb-3" />
          <p className="text-gray-700 dark:text-gray-300 font-medium">AI Unavailable</p>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {data.message || 'No AI provider is configured. Please check your settings.'}
          </p>
        </motion.div>
      )}

      {!isPending && data?.available && data.answer && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-4"
        >
          <div className="card p-6">
            <div className="flex items-center gap-2 mb-3">
              <Brain className="h-5 w-5 text-brand-500" />
              <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Answer</h3>
            </div>
            <div className="text-sm text-gray-900 dark:text-white leading-relaxed whitespace-pre-wrap">
              {data.answer}
            </div>
          </div>
          {data.calculated_facts && Object.keys(data.calculated_facts).length > 0 && (
            <FactsDisplay facts={data.calculated_facts} />
          )}
        </motion.div>
      )}
    </div>
  );
}
