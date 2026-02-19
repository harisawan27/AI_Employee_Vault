'use client';

import { useState, useEffect, useCallback } from 'react';
import { X, Check, XCircle, Save } from 'lucide-react';
import { updateApprovalContent, approveItem, rejectItem } from '@/lib/api';

interface ApprovalEditorProps {
  item: {
    id: string;
    filename: string;
    domain: string;
    metadata: Record<string, string>;
    content: string;
  };
  onClose: () => void;
  onAction: () => void;
}

export default function ApprovalEditor({ item, onClose, onAction }: ApprovalEditorProps) {
  const [content, setContent] = useState(item.content);
  const [saving, setSaving] = useState(false);
  const [acting, setActing] = useState<string | null>(null);
  const [message, setMessage] = useState('');

  const handleSave = useCallback(async () => {
    setSaving(true);
    try {
      await updateApprovalContent(item.id, content);
      setMessage('Draft saved');
      setTimeout(() => setMessage(''), 2000);
    } catch {
      setMessage('Save failed');
    } finally {
      setSaving(false);
    }
  }, [item.id, content]);

  const handleApprove = useCallback(async () => {
    setActing('approve');
    try {
      await approveItem(item.id);
      onAction();
      onClose();
    } catch {
      setMessage('Approve failed');
      setActing(null);
    }
  }, [item.id, onAction, onClose]);

  const handleReject = async () => {
    setActing('reject');
    try {
      await rejectItem(item.id);
      onAction();
      onClose();
    } catch {
      setMessage('Reject failed');
      setActing(null);
    }
  };

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
      if (e.ctrlKey && e.key === 'Enter') handleApprove();
      if (e.ctrlKey && e.key === 's') {
        e.preventDefault();
        handleSave();
      }
    };
    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [onClose, handleApprove, handleSave]);

  const domainColor = {
    email: 'bg-blue-100 text-blue-700',
    social_media: 'bg-purple-100 text-purple-700',
    payments: 'bg-green-100 text-green-700',
  }[item.domain] || 'bg-gray-100 text-gray-700';

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl shadow-2xl w-full max-w-5xl max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-3 sm:p-4 border-b">
          <div className="flex items-center gap-2 sm:gap-3 min-w-0">
            <h2 className="font-semibold text-base sm:text-lg truncate">{item.filename}</h2>
            <span className={`text-xs px-2 py-1 rounded-full font-medium flex-shrink-0 ${domainColor}`}>
              {item.domain}
            </span>
          </div>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 rounded-lg transition">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content area — split pane */}
        <div className="flex-1 grid grid-cols-1 lg:grid-cols-2 gap-0 overflow-hidden">
          {/* Preview pane */}
          <div className="p-4 sm:p-6 overflow-y-auto border-r border-gray-100">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Preview</h3>
            {/* Metadata */}
            {Object.entries(item.metadata).length > 0 && (
              <div className="mb-4 p-3 bg-gray-50 rounded-lg text-sm space-y-1">
                {Object.entries(item.metadata).map(([k, v]) => (
                  <div key={k} className="flex gap-2">
                    <span className="text-gray-500 font-medium">{k}:</span>
                    <span className="text-gray-700">{v}</span>
                  </div>
                ))}
              </div>
            )}
            {/* Rendered content */}
            <div className="prose prose-sm max-w-none whitespace-pre-wrap text-gray-800">
              {content}
            </div>
          </div>

          {/* Editor pane */}
          <div className="p-4 sm:p-6 flex flex-col overflow-hidden">
            <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wide mb-3">Edit</h3>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="flex-1 w-full p-4 border border-gray-200 rounded-lg resize-none font-mono text-sm focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none"
              placeholder="Edit content..."
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center justify-between p-3 sm:p-4 gap-3 border-t bg-gray-50 rounded-b-2xl">
          <div className="text-sm text-gray-500">
            {message && <span className="text-brand-600 font-medium">{message}</span>}
            {!message && (
              <span className="hidden sm:inline space-x-3">
                <kbd className="px-1.5 py-0.5 bg-gray-200 rounded text-xs font-mono">Ctrl+S</kbd>
                <span>Save</span>
                <kbd className="px-1.5 py-0.5 bg-gray-200 rounded text-xs font-mono ml-2">Ctrl+Enter</kbd>
                <span>Approve</span>
                <kbd className="px-1.5 py-0.5 bg-gray-200 rounded text-xs font-mono ml-2">Esc</kbd>
                <span>Close</span>
              </span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleSave}
              disabled={saving}
              className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-3 sm:px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-100 transition disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {saving ? 'Saving...' : 'Save'}
            </button>
            <button
              onClick={handleReject}
              disabled={acting !== null}
              className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-3 sm:px-4 py-2 text-sm bg-red-500 text-white rounded-lg hover:bg-red-600 transition disabled:opacity-50"
            >
              <XCircle className="w-4 h-4" />
              {acting === 'reject' ? 'Rejecting...' : 'Reject'}
            </button>
            <button
              onClick={handleApprove}
              disabled={acting !== null}
              className="flex-1 sm:flex-none flex items-center justify-center gap-2 px-3 sm:px-4 py-2 text-sm bg-green-500 text-white rounded-lg hover:bg-green-600 transition disabled:opacity-50"
            >
              <Check className="w-4 h-4" />
              {acting === 'approve' ? 'Approving...' : 'Approve'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
