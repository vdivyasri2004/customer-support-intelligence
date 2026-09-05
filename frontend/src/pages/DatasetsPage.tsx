import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Database, Upload, Play, Trash2, FileText, MessageSquare, Brain } from 'lucide-react'
import toast from 'react-hot-toast'
import { datasetsAPI } from '../services/api'

export default function DatasetsPage() {
  const queryClient = useQueryClient()
  const navigate = useNavigate()

  const { data, isLoading } = useQuery({
    queryKey: ['datasets'],
    queryFn: datasetsAPI.list,
  })
  const datasets = data?.datasets || []

  const loadSampleMutation = useMutation({
    mutationFn: datasetsAPI.loadSample,
    onSuccess: () => {
      toast.success('Sample dataset loaded successfully')
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
    },
    onError: () => {
      toast.error('Failed to load sample dataset')
    },
  })

  const uploadMutation = useMutation({
    mutationFn: datasetsAPI.upload,
    onSuccess: (data) => {
      toast.success('Dataset uploaded successfully')
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
    },
    onError: () => {
      toast.error('Failed to upload dataset')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => datasetsAPI.delete(id),
    onSuccess: () => {
      toast.success('Dataset deleted')
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
    },
    onError: () => {
      toast.error('Failed to delete dataset')
    },
  })

  const handleUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return
    uploadMutation.mutate(file)
    e.target.value = ''
  }

  const handleDelete = (id: number, name: string) => {
    if (window.confirm(`Delete dataset "${name}"?`)) {
      deleteMutation.mutate(id)
    }
  }

  const selectedDatasetId = Number(localStorage.getItem('selectedDatasetId'))

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading datasets...</div>
      </div>
    )
  }

  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Datasets</h1>
          <p className="text-gray-500 mt-1">Manage your support ticket datasets</p>
        </div>
        <div className="flex gap-3">
          <button
            className="btn-secondary flex items-center gap-2"
            onClick={() => loadSampleMutation.mutate()}
            disabled={loadSampleMutation.isPending}
          >
            <Database size={16} />
            {loadSampleMutation.isPending ? 'Loading...' : 'Load Sample Dataset'}
          </button>
          <button
            className="btn-primary flex items-center gap-2"
            onClick={() => document.getElementById('csv-upload')?.click()}
          >
            <Upload size={16} />
            Upload CSV
          </button>
          <input
            id="csv-upload"
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleUpload}
          />
        </div>
      </div>

      {datasets.length === 0 ? (
        <div className="text-center py-16">
          <Database size={48} className="mx-auto text-gray-300 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No datasets</h3>
          <p className="text-gray-500 mb-6">Get started by loading a sample dataset or uploading your own CSV.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {datasets.map((dataset: any) => (
            <motion.div
              key={dataset.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`card ${dataset.id === selectedDatasetId ? 'ring-2 ring-blue-500' : ''}`}
            >
              <div className="p-5">
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-900 truncate">{dataset.name}</h3>
                    <span
                      className={`inline-block text-xs font-medium px-2 py-0.5 rounded-full mt-1 ${
                        dataset.source_type === 'sample'
                          ? 'bg-green-100 text-green-700'
                          : 'bg-blue-100 text-blue-700'
                      }`}
                    >
                      {dataset.source_type}
                    </span>
                  </div>
                </div>

                <div className="space-y-1 text-sm text-gray-500 mb-4">
                  {dataset.original_filename && (
                    <div className="flex items-center gap-1.5">
                      <FileText size={14} />
                      <span className="truncate">{dataset.original_filename}</span>
                    </div>
                  )}
                  <div>{dataset.row_count?.toLocaleString()} rows</div>
                  <div>Created {formatDate(dataset.created_at)}</div>
                </div>

                <div className="flex gap-2">
                  <button
                    className="btn-primary text-xs px-3 py-1.5 flex items-center gap-1"
                    onClick={() => {
                      localStorage.setItem('selectedDatasetId', String(dataset.id))
                      navigate('/dashboard')
                    }}
                  >
                    <Play size={12} />
                    Dashboard
                  </button>
                  <button
                    className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1"
                    onClick={() => navigate(`/datasets/${dataset.id}/tickets`)}
                  >
                    <MessageSquare size={12} />
                    Tickets
                  </button>
                  <button
                    className="btn-secondary text-xs px-3 py-1.5 flex items-center gap-1"
                    onClick={() => navigate(`/datasets/${dataset.id}/insights`)}
                  >
                    <Brain size={12} />
                    Insights
                  </button>
                  <button
                    className="text-xs px-2 py-1.5 text-red-500 hover:bg-red-50 rounded flex items-center gap-1"
                    onClick={() => handleDelete(dataset.id, dataset.name)}
                    disabled={deleteMutation.isPending}
                  >
                    <Trash2 size={12} />
                  </button>
                </div>
              </div>
            </motion.div>
          ))}
        </div>
      )}
    </div>
  )
}
