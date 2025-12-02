import { User, Session } from '@supabase/supabase-js'

export interface UserProfile {
  id: string
  email: string
  role: 'admin' | 'manager' | 'viewer'
  full_name?: string
  avatar_url?: string
  created_at: string
  updated_at: string
}

export interface AuthState {
  user: User | null
  session: Session | null
  loading: boolean
}

export type UserRole = 'admin' | 'manager' | 'viewer'
