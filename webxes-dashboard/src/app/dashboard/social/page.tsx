'use client';

import { useState, useRef, useEffect } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { generateSocialPost, getApprovals, getApproval } from '@/lib/api';
import {
  Send,
  Sparkles,
  Linkedin,
  Facebook,
  Instagram,
  Twitter,
  Share2,
  ArrowRight,
  CheckCircle,
  Clock,
} from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';
import ApprovalEditor from '@/components/ApprovalEditor';

const platformIcons: Record<string, any> = {
  linkedin: Linkedin,
  facebook: Facebook,
  instagram: Instagram,
  twitter: Twitter,
};

const platformColors: Record<string, string> = {
  linkedin: 'bg-blue-600',
  facebook: 'bg-blue-500',
  instagram: 'bg-pink-500',
  twitter: 'bg-gray-900',
};

const platformBadgeColors: Record<string, string> = {
  linkedin: 'bg-blue-100 text-blue-700',
  facebook: 'bg-blue-50 text-blue-600',
  instagram: 'bg-pink-100 text-pink-700',
  twitter: 'bg-gray-100 text-gray-700',
};

const quickPrompts = [
  { label: 'LinkedIn', prompt: 'LinkedIn post about ', platform: 'linkedin' },
  { label: 'Facebook', prompt: 'Facebook post about ', platform: 'facebook' },
  { label: 'Instagram', prompt: 'Instagram post about ', platform: 'instagram' },
  { label: 'Twitter', prompt: 'Tweet about ', platform: 'twitter' },
];

interface GeneratedPost {
  id: string;
  platform: string;
  content: string;
  filename: string;
  timestamp: Date;
}

export default function SocialPage() {
  const [message, setMessage] = useState('');
  const [isGenerating, setIsGenerating] = useState(false);
  const [generatedPosts, setGeneratedPosts] = useState<GeneratedPost[]>([]);
  const [error, setError] = useState('');
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const queryClient = useQueryClient();

  // Fetch existing social media approvals
  const { data: approvals } = useQuery({
    queryKey: ['approvals', 'social_media'],
    queryFn: () => getApprovals({ domain: 'social_media' }).then((r) => r.data),
    refetchInterval: 15_000,
  });

  // Auto-focus input
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleGenerate = async () => {
    if (!message.trim() || isGenerating) return;

    setError('');
    setIsGenerating(true);

    try {
      const res = await generateSocialPost(message.trim());
      const post = res.data;
      setGeneratedPosts((prev) => [
        { ...post, timestamp: new Date() },
        ...prev,
      ]);
      setMessage('');
      // Refresh approvals list
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to generate post. Check your API key.');
    } finally {
      setIsGenerating(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleGenerate();
    }
  };

  const handleQuickPrompt = (prompt: string) => {
    setMessage(prompt);
    inputRef.current?.focus();
  };

  const handleOpenApproval = async (item: any) => {
    try {
      const res = await getApproval(item.id);
      setSelectedItem(res.data);
    } catch {
      // ignore
    }
  };

  const handleAction = () => {
    queryClient.invalidateQueries({ queryKey: ['approvals'] });
    queryClient.invalidateQueries({ queryKey: ['dashboard-stats'] });
  };

  // Detect platform from current message for visual hint
  const detectPlatform = (msg: string): string | null => {
    const lower = msg.toLowerCase();
    if (lower.includes('linkedin')) return 'linkedin';
    if (lower.includes('facebook') || lower.includes('fb ')) return 'facebook';
    if (lower.includes('instagram') || lower.includes('insta') || lower.includes('ig ')) return 'instagram';
    if (lower.includes('twitter') || lower.includes('tweet')) return 'twitter';
    return null;
  };

  const detectedPlatform = detectPlatform(message);
  const DetectedIcon = detectedPlatform ? platformIcons[detectedPlatform] : Sparkles;

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold mb-2">Social Media</h1>
      <p className="text-gray-500 text-sm mb-6">
        Tell the AI what to post — it generates, you approve, it publishes.
      </p>

      {/* Message Bar */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 mb-6">
        {/* Quick platform buttons */}
        <div className="flex gap-2 mb-3 overflow-x-auto pb-1">
          {quickPrompts.map((qp) => {
            const Icon = platformIcons[qp.platform];
            return (
              <button
                key={qp.platform}
                onClick={() => handleQuickPrompt(qp.prompt)}
                className={`flex items-center gap-1.5 px-3 py-1.5 text-xs rounded-full border transition hover:shadow-sm flex-shrink-0 ${
                  detectedPlatform === qp.platform
                    ? `${platformBadgeColors[qp.platform]} border-current font-medium`
                    : 'border-gray-200 text-gray-500 hover:border-gray-300'
                }`}
              >
                <Icon className="w-3.5 h-3.5" />
                {qp.label}
              </button>
            );
          })}
        </div>

        {/* Input area */}
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder='e.g. "LinkedIn post about our new web design service launching next week"'
              rows={2}
              className="w-full border border-gray-200 rounded-lg px-4 py-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent placeholder:text-gray-400"
            />
            {detectedPlatform && (
              <div className={`absolute top-2 right-2 px-2 py-0.5 rounded-full text-xs ${platformBadgeColors[detectedPlatform]}`}>
                {detectedPlatform}
              </div>
            )}
          </div>
          <button
            onClick={handleGenerate}
            disabled={!message.trim() || isGenerating}
            className="self-stretch sm:self-end px-5 py-3 bg-brand-600 text-white rounded-lg hover:bg-brand-700 disabled:opacity-50 disabled:cursor-not-allowed transition flex items-center justify-center gap-2 text-sm font-medium"
          >
            {isGenerating ? (
              <>
                <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full" />
                Generating...
              </>
            ) : (
              <>
                <Send className="w-4 h-4" />
                Generate
              </>
            )}
          </button>
        </div>
        <p className="text-xs text-gray-400 mt-2">
          Press Enter to generate. Shift+Enter for new line. The post will appear in your approval queue.
        </p>

        {/* Error */}
        {error && (
          <div className="mt-3 px-3 py-2 bg-red-50 text-red-600 text-sm rounded-lg">
            {error}
          </div>
        )}
      </div>

      {/* Just Generated */}
      {generatedPosts.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-500" />
            Just Generated
          </h2>
          <div className="space-y-3">
            {generatedPosts.map((post, i) => {
              const PlatIcon = platformIcons[post.platform] || Share2;
              return (
                <div
                  key={`${post.id}-${i}`}
                  className="bg-white rounded-xl shadow-sm border border-gray-100 border-l-4 border-l-purple-500 p-5"
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className={`p-1.5 rounded-lg ${platformColors[post.platform] || 'bg-gray-500'}`}>
                        <PlatIcon className="w-4 h-4 text-white" />
                      </div>
                      <span className="font-medium text-gray-900 capitalize">{post.platform}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full bg-yellow-100 text-yellow-700`}>
                        <Clock className="w-3 h-3 inline mr-1" />
                        Pending Approval
                      </span>
                    </div>
                    <span className="text-xs text-gray-400">Just now</span>
                  </div>
                  <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">
                    {post.content}
                  </p>
                  <div className="mt-4 flex justify-end">
                    <button
                      onClick={() => handleOpenApproval({ id: post.id })}
                      className="flex items-center gap-1.5 text-sm text-brand-600 hover:text-brand-700 font-medium"
                    >
                      Review & Approve
                      <ArrowRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Pending Social Media Approvals */}
      <div>
        <h2 className="text-lg font-semibold mb-3 flex items-center gap-2">
          <Clock className="w-5 h-5 text-orange-500" />
          Pending Social Posts
          {approvals?.items?.length > 0 && (
            <span className="text-xs px-2 py-0.5 rounded-full bg-orange-100 text-orange-700">
              {approvals.items.length}
            </span>
          )}
        </h2>

        {approvals?.items?.length === 0 && (
          <div className="text-center py-12 bg-white rounded-xl shadow-sm border border-gray-100">
            <Share2 className="w-10 h-10 text-gray-300 mx-auto mb-2" />
            <p className="text-gray-400 text-sm">No pending social media posts</p>
            <p className="text-gray-300 text-xs mt-1">Use the message bar above to generate one</p>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {approvals?.items?.map((item: any) => {
            const platform = item.metadata?.platform || 'unknown';
            const PlatIcon = platformIcons[platform] || Share2;
            return (
              <button
                key={item.id}
                onClick={() => handleOpenApproval(item)}
                className="text-left bg-white rounded-xl shadow-sm border border-gray-100 border-l-4 border-l-purple-500 p-5 hover:shadow-md transition cursor-pointer"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <div className={`p-1.5 rounded-lg ${platformColors[platform] || 'bg-gray-500'}`}>
                      <PlatIcon className="w-3.5 h-3.5 text-white" />
                    </div>
                    <span className="font-medium text-gray-900 text-sm capitalize">{platform}</span>
                  </div>
                  <span className="text-xs text-gray-400">
                    {item.modified
                      ? formatDistanceToNow(new Date(item.modified * 1000), { addSuffix: true })
                      : ''}
                  </span>
                </div>
                <p className="text-sm text-gray-500 line-clamp-3">{item.preview}</p>
                {item.metadata?.topic && (
                  <div className="mt-2">
                    <span className="text-xs px-2 py-0.5 rounded-full bg-purple-50 text-purple-600">
                      {item.metadata.topic}
                    </span>
                  </div>
                )}
              </button>
            );
          })}
        </div>
      </div>

      {/* Approval Editor Modal */}
      {selectedItem && (
        <ApprovalEditor
          item={selectedItem}
          onClose={() => setSelectedItem(null)}
          onAction={handleAction}
        />
      )}
    </div>
  );
}
