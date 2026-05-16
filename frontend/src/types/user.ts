export interface UserOut {
  id: string;
  name: string;
  email: string;
  role: string;
  status: string;
  created_at: string;
}

export interface UserCreate {
  name: string;
  email: string;
  password: string;
  role: string;
}

export interface UserUpdate {
  name?: string;
  email?: string;
  password?: string;
  role?: string;
  status?: string;
}
