import { create } from 'zustand'

interface AuthState {
  token: string | null
  setToken: (token: string | null) => void
  clearAuth: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  setToken: (token) => set({ token }),
  clearAuth: () => set({ token: null }),
}))
