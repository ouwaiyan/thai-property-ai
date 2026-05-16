export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RefreshRequest {
  refresh_token: string;
}

export interface UserMe {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  status: UserStatus;
  created_at: string;
}

export type UserRole = 'Admin' | 'Manager' | 'Agent' | 'Viewer';
export type UserStatus = 'active' | 'inactive';
