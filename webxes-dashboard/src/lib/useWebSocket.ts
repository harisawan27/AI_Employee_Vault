'use client';

import { useEffect, useRef, useCallback } from 'react';
import { create } from 'zustand';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:5000';

interface WSEvent {
  type: string;
  file?: string;
  path?: string;
  action?: string;
}

interface NotificationStore {
  events: WSEvent[];
  unreadCount: number;
  addEvent: (event: WSEvent) => void;
  clearUnread: () => void;
}

export const useNotificationStore = create<NotificationStore>((set) => ({
  events: [],
  unreadCount: 0,
  addEvent: (event) =>
    set((state) => ({
      events: [event, ...state.events].slice(0, 50),
      unreadCount: state.unreadCount + 1,
    })),
  clearUnread: () => set({ unreadCount: 0 }),
}));

export function useWebSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const addEvent = useNotificationStore((s) => s.addEvent);

  const connect = useCallback(() => {
    const token = localStorage.getItem('webxes_token');
    if (!token) return;

    const ws = new WebSocket(`${WS_URL}/api/ws?token=${token}`);

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type !== 'pong') {
          addEvent(data);
        }
      } catch {
        // ignore parse errors
      }
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected, reconnecting in 5s...');
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
    };

    wsRef.current = ws;

    return () => {
      clearInterval(pingInterval);
      ws.close();
    };
  }, [addEvent]);

  useEffect(() => {
    const cleanup = connect();
    return () => cleanup?.();
  }, [connect]);

  return wsRef;
}
