'use client';

import { useEffect, useRef, useCallback } from 'react';
import { create } from 'zustand';
import { useToastStore } from '@/components/Toast';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:5000';

interface WSEvent {
  type: string;
  file?: string;
  path?: string;
  action?: string;
  timestamp?: string;
}

interface NotificationStore {
  events: WSEvent[];
  unreadCount: number;
  connected: boolean;
  addEvent: (event: WSEvent) => void;
  clearUnread: () => void;
  clearAll: () => void;
  removeEvent: (index: number) => void;
  setConnected: (connected: boolean) => void;
}

export const useNotificationStore = create<NotificationStore>((set) => ({
  events: [],
  unreadCount: 0,
  connected: false,
  addEvent: (event) =>
    set((state) => ({
      events: [{ ...event, timestamp: event.timestamp || new Date().toISOString() }, ...state.events].slice(0, 50),
      unreadCount: state.unreadCount + 1,
    })),
  clearUnread: () => set({ unreadCount: 0 }),
  clearAll: () => set({ events: [], unreadCount: 0 }),
  removeEvent: (index) =>
    set((state) => ({
      events: state.events.filter((_, i) => i !== index),
    })),
  setConnected: (connected) => set({ connected }),
}));

function getToastMessage(data: WSEvent): string {
  const file = data.file || data.path || '';
  const shortFile = file ? file.split('/').pop() || file : '';
  const action = data.action || data.type || 'Event';

  if (data.type === 'new_approval' || action.includes('approval')) {
    return `New approval added: ${shortFile}`;
  }
  if (data.type === 'file_change') {
    return `File updated: ${shortFile}`;
  }
  if (data.type === 'email' || action.includes('email')) {
    return `New email: ${shortFile}`;
  }
  if (shortFile) {
    return `${action}: ${shortFile}`;
  }
  return action;
}

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const addEvent = useNotificationStore((s) => s.addEvent);
  const setConnected = useNotificationStore((s) => s.setConnected);

  const connect = useCallback(() => {
    const token = localStorage.getItem('webxes_token');
    if (!token) return;

    const ws = new WebSocket(`${WS_URL}/api/ws?token=${token}`);

    ws.onopen = () => {
      console.log('WebSocket connected');
      setConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type !== 'pong') {
          addEvent(data);
          const msg = getToastMessage(data);
          useToastStore.getState().addToast('info', msg);
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected, reconnecting in 5s...');
      setConnected(false);
      setTimeout(connect, 5000);
    };

    // Ping every 30s to keep alive
    const pingInterval = setInterval(() => {
      if (ws.readyState === WebSocket.OPEN) {
        ws.send('ping');
      }
    }, 30000);

    ws.onerror = () => {
      clearInterval(pingInterval);
      setConnected(false);
    };

    wsRef.current = ws;

    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  }, [addEvent, setConnected]);

  useEffect(() => {
    const cleanup = connect();
    return () => cleanup?.();
  }, [connect]);

  return wsRef;
}
