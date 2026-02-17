'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { checkAuth } from './api';

export function useAuth() {
  const [authenticated, setAuthenticated] = useState(false);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useEffect(() => {
    const token = localStorage.getItem('webxes_token');
    if (!token) {
      setLoading(false);
      router.push('/login');
      return;
    }

    checkAuth()
      .then(() => {
        setAuthenticated(true);
        setLoading(false);
      })
      .catch(() => {
        localStorage.removeItem('webxes_token');
        setLoading(false);
        router.push('/login');
      });
  }, [router]);

  const logout = () => {
    localStorage.removeItem('webxes_token');
    setAuthenticated(false);
    router.push('/login');
  };

  return { authenticated, loading, logout };
}
