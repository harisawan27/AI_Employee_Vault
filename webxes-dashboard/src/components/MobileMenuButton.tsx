'use client';

import { Menu } from 'lucide-react';

interface MobileMenuButtonProps {
  onClick: () => void;
}

export default function MobileMenuButton({ onClick }: MobileMenuButtonProps) {
  return (
    <button
      onClick={onClick}
      className="fixed top-4 left-4 z-[55] p-2 bg-brand-900 text-white rounded-lg shadow-lg lg:hidden"
      aria-label="Open menu"
    >
      <Menu className="w-5 h-5" />
    </button>
  );
}
