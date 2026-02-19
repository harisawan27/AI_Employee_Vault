'use client';

import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getSettings, toggleDryRun } from '@/lib/api';
import { Settings, AlertTriangle, Server, Shield, Bell, Info, LogOut, ExternalLink } from 'lucide-react';

export default function SettingsPage() {
  const [confirmModal, setConfirmModal] = useState(false);
  const [pendingValue, setPendingValue] = useState(false);
  const queryClient = useQueryClient();

  // Notification prefs from localStorage
  const [emailAlerts, setEmailAlerts] = useState(() =>
    typeof window !== 'undefined' ? localStorage.getItem('notif_email_alerts') === 'true' : false
  );
  const [webhookUrl, setWebhookUrl] = useState(() =>
    typeof window !== 'undefined' ? localStorage.getItem('notif_webhook_url') || '' : ''
  );

  const { data: settings, isLoading } = useQuery({
    queryKey: ['settings'],
    queryFn: () => getSettings().then((r) => r.data),
  });

  const mutation = useMutation({
    mutationFn: (enabled: boolean) => toggleDryRun(enabled),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] });
      setConfirmModal(false);
    },
  });

  const handleToggle = (newValue: boolean) => {
    setPendingValue(newValue);
    setConfirmModal(true);
  };

  const handleEmailAlertsToggle = () => {
    const next = !emailAlerts;
    setEmailAlerts(next);
    localStorage.setItem('notif_email_alerts', String(next));
  };

  const handleWebhookSave = () => {
    localStorage.setItem('notif_webhook_url', webhookUrl);
  };

  const handleLogoutAll = () => {
    localStorage.removeItem('webxes_token');
    window.location.href = '/login';
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <div className="animate-spin h-8 w-8 border-4 border-brand-500 border-t-transparent rounded-full" />
      </div>
    );
  }

  const loginTimestamp = typeof window !== 'undefined' ? localStorage.getItem('webxes_login_ts') : null;

  return (
    <div className="max-w-3xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Settings</h1>

      {/* DRY_RUN toggle */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="p-3 bg-yellow-50 rounded-lg">
              <Shield className="w-6 h-6 text-yellow-600" />
            </div>
            <div>
              <h3 className="font-semibold">Dry Run Mode</h3>
              <p className="text-sm text-gray-500">
                When enabled, actions are simulated without real side effects
              </p>
            </div>
          </div>
          <button
            onClick={() => handleToggle(!settings?.dry_run)}
            className={`relative w-14 h-7 rounded-full transition-colors ${
              settings?.dry_run ? 'bg-green-500' : 'bg-gray-300'
            }`}
          >
            <span
              className={`absolute top-0.5 w-6 h-6 bg-white rounded-full shadow transition-transform ${
                settings?.dry_run ? 'translate-x-7' : 'translate-x-0.5'
              }`}
            />
          </button>
        </div>
      </div>

      {/* System info */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
        <div className="flex items-center gap-3 mb-4">
          <Server className="w-5 h-5 text-gray-500" />
          <h3 className="font-semibold">System Information</h3>
        </div>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between py-2 border-b border-gray-50">
            <span className="text-gray-500">Vault Path</span>
            <span className="font-mono text-gray-900">{settings?.vault_path}</span>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-50">
            <span className="text-gray-500">Work Zone</span>
            <span className="font-medium text-gray-900">{settings?.work_zone}</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-gray-500">Cloud Mode</span>
            <span className={`font-medium ${settings?.is_cloud ? 'text-blue-600' : 'text-gray-600'}`}>
              {settings?.is_cloud ? 'Cloud' : 'Local'}
            </span>
          </div>
        </div>
      </div>

      {/* Notification Preferences */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
        <div className="flex items-center gap-3 mb-4">
          <Bell className="w-5 h-5 text-gray-500" />
          <h3 className="font-semibold">Notification Preferences</h3>
        </div>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-700">Email Alerts</p>
              <p className="text-xs text-gray-400">Receive email notifications for important events</p>
            </div>
            <button
              onClick={handleEmailAlertsToggle}
              className={`relative w-12 h-6 rounded-full transition-colors ${
                emailAlerts ? 'bg-brand-500' : 'bg-gray-300'
              }`}
            >
              <span
                className={`absolute top-0.5 w-5 h-5 bg-white rounded-full shadow transition-transform ${
                  emailAlerts ? 'translate-x-6' : 'translate-x-0.5'
                }`}
              />
            </button>
          </div>
          <div>
            <label className="text-sm font-medium text-gray-700 block mb-1">Webhook URL</label>
            <div className="flex gap-2">
              <input
                type="url"
                value={webhookUrl}
                onChange={(e) => setWebhookUrl(e.target.value)}
                placeholder="https://hooks.example.com/notify"
                className="flex-1 px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-brand-500 focus:border-transparent outline-none"
              />
              <button
                onClick={handleWebhookSave}
                className="px-4 py-2 bg-brand-600 text-white text-sm rounded-lg hover:bg-brand-700 transition"
              >
                Save
              </button>
            </div>
            <p className="text-xs text-gray-400 mt-1">Optional: POST notifications to an external endpoint</p>
          </div>
        </div>
      </div>

      {/* Session Info */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-6">
        <div className="flex items-center gap-3 mb-4">
          <LogOut className="w-5 h-5 text-gray-500" />
          <h3 className="font-semibold">Session</h3>
        </div>
        <div className="space-y-3 text-sm">
          {loginTimestamp && (
            <div className="flex justify-between py-2 border-b border-gray-50">
              <span className="text-gray-500">Login Time</span>
              <span className="text-gray-900">{new Date(loginTimestamp).toLocaleString()}</span>
            </div>
          )}
          <div className="flex justify-between py-2 border-b border-gray-50">
            <span className="text-gray-500">Token Status</span>
            <span className="text-green-600 font-medium">Active</span>
          </div>
          <button
            onClick={handleLogoutAll}
            className="mt-2 px-4 py-2 text-sm text-red-600 border border-red-200 rounded-lg hover:bg-red-50 transition"
          >
            Log out all sessions
          </button>
        </div>
      </div>

      {/* About */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center gap-3 mb-4">
          <Info className="w-5 h-5 text-gray-500" />
          <h3 className="font-semibold">About</h3>
        </div>
        <div className="space-y-3 text-sm">
          <div className="flex justify-between py-2 border-b border-gray-50">
            <span className="text-gray-500">Version</span>
            <span className="font-mono text-gray-900">1.0.0</span>
          </div>
          <div className="flex justify-between py-2 border-b border-gray-50">
            <span className="text-gray-500">Built by</span>
            <span className="text-gray-900 font-medium">WEBXES Tech</span>
          </div>
          <div className="flex justify-between py-2">
            <span className="text-gray-500">Source</span>
            <a
              href="https://github.com/webxes-tech"
              target="_blank"
              rel="noopener noreferrer"
              className="text-brand-600 hover:text-brand-700 flex items-center gap-1"
            >
              GitHub <ExternalLink className="w-3 h-3" />
            </a>
          </div>
        </div>
      </div>

      {/* Confirmation modal */}
      {confirmModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl shadow-2xl p-6 max-w-md mx-4">
            <div className="flex items-center gap-3 mb-4">
              <AlertTriangle className="w-6 h-6 text-yellow-500" />
              <h3 className="font-semibold text-lg">Confirm Change</h3>
            </div>
            <p className="text-gray-600 mb-6">
              {pendingValue
                ? 'Enable Dry Run mode? Actions will be simulated only.'
                : 'Disable Dry Run mode? Actions will have real effects (send emails, post to social media, etc).'}
            </p>
            <div className="flex gap-3 justify-end">
              <button
                onClick={() => setConfirmModal(false)}
                className="px-4 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={() => mutation.mutate(pendingValue)}
                disabled={mutation.isPending}
                className="px-4 py-2 text-sm bg-brand-600 text-white rounded-lg hover:bg-brand-700 disabled:opacity-50"
              >
                {mutation.isPending ? 'Updating...' : 'Confirm'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
