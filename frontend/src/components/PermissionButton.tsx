'use client';

import { useAuthStore } from '@/stores/authStore';
import { hasRole } from '@/lib/permissions';
import type { UserRole } from '@/types/auth';

interface Props {
  requiredRole: UserRole;
  children: React.ReactNode;
  fallback?: React.ReactNode;
}

export default function PermissionButton({ requiredRole, children, fallback = null }: Props) {
  const user = useAuthStore((s) => s.user);
  if (!user || !hasRole(user.role as UserRole, requiredRole)) return <>{fallback}</>;
  return <>{children}</>;
}
