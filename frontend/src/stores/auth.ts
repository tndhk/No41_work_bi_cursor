import { create } from 'zustand'
import { UserResponse } from '../lib/api'

interface AuthState {
  token: string | null
  user: UserResponse | null
  setToken: (token: string | null) => void
  setUser: (user: UserResponse | null) => void
  clearAuth: () => void
  isAuthenticated: () => boolean
}

export const useAuthStore = create<AuthState>((set, get) => ({
  token: localStorage.getItem('auth_token'),
  user: null,
  setToken: (token) => {
    if (token) {
      localStorage.setItem('auth_token', token)
    } else {
      localStorage.removeItem('auth_token')
    }
    set({ token })
  },
  setUser: (user) => set({ user }),
  clearAuth: () => {
    localStorage.removeItem('auth_token')
    set({ token: null, user: null })
  },
  isAuthenticated: () => {
    return !!get().token
  },
}))
