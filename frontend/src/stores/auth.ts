import { create } from 'zustand'
import { UserResponse } from '../types/auth'

interface AuthState {
  user: UserResponse | null
  setUser: (user: UserResponse | null) => void
  clearAuth: () => void
  isAuthenticated: () => boolean
  authChecked: boolean
  setAuthChecked: (checked: boolean) => void
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  setUser: (user) => set({ user }),
  clearAuth: () => {
    set({ user: null, authChecked: true })
  },
  isAuthenticated: () => {
    return !!get().user
  },
  authChecked: false,
  setAuthChecked: (checked) => set({ authChecked: checked }),
}))
