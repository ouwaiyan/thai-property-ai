import type { UserRole } from '@/types/auth';

const ROLE_HIERARCHY: Record<UserRole, number> = {
  Admin: 4,
  Manager: 3,
  Agent: 2,
  Viewer: 1,
};

export function hasRole(userRole: string | null, required: UserRole): boolean {
  if (!userRole) return false;
  const userLevel = ROLE_HIERARCHY[userRole as UserRole] ?? 0;
  const requiredLevel = ROLE_HIERARCHY[required];
  return userLevel >= requiredLevel;
}

export function canEditProperty(userRole: string | null, createdBy: string, userId: string): boolean {
  if (!userRole) return false;
  if (hasRole(userRole, 'Manager')) return true;
  if (userRole === 'Agent' && createdBy === userId) return true;
  return false;
}

export function canDeleteProperty(userRole: string | null): boolean {
  return hasRole(userRole, 'Manager');
}
