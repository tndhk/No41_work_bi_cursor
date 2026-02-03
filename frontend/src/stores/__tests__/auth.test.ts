import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from '../auth'
import type { UserResponse } from '../../lib/api'

describe('useAuthStore', () => {
  beforeEach(() => {
    // 各テスト前にストアをリセット
    useAuthStore.setState({
      user: null,
      authChecked: false,
    })
  })

  describe('初期状態', () => {
    it('ストアの初期状態を確認できる', () => {
      useAuthStore.setState({ user: null, authChecked: false })
      const state = useAuthStore.getState()
      expect(state.user).toBeNull()
      expect(state.authChecked).toBe(false)
    })
  })

  describe('setUser', () => {
    it('ユーザー情報を設定できる', () => {
      const mockUser: UserResponse = {
        user_id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
      }
      
      useAuthStore.getState().setUser(mockUser)
      
      expect(useAuthStore.getState().user).toEqual(mockUser)
    })

    it('null を設定してユーザー情報をクリアできる', () => {
      // まずユーザーを設定
      const mockUser: UserResponse = {
        user_id: 'user-123',
        email: 'test@example.com',
        name: 'Test User',
      }
      useAuthStore.getState().setUser(mockUser)
      
      // null を設定
      useAuthStore.getState().setUser(null)
      
      expect(useAuthStore.getState().user).toBeNull()
    })
  })

  describe('clearAuth', () => {
    it('認証情報をクリアするとユーザーが null になる', () => {
      // 初期状態を設定
      useAuthStore.setState({
        user: {
          user_id: 'user-123',
          email: 'test@example.com',
          name: 'Test User',
        },
        authChecked: false,
      })
      
      useAuthStore.getState().clearAuth()
      
      expect(useAuthStore.getState().user).toBeNull()
      expect(useAuthStore.getState().authChecked).toBe(true)
    })

    it('既にクリア済みの状態でもエラーにならない', () => {
      useAuthStore.setState({
        user: null,
        authChecked: true,
      })
      
      expect(() => {
        useAuthStore.getState().clearAuth()
      }).not.toThrow()
      
      expect(useAuthStore.getState().user).toBeNull()
      expect(useAuthStore.getState().authChecked).toBe(true)
    })
  })

  describe('isAuthenticated', () => {
    it('ユーザーがある場合は true を返す', () => {
      useAuthStore.setState({
        user: {
          user_id: 'user-123',
          email: 'test@example.com',
          name: 'Test User',
        },
      })
      
      expect(useAuthStore.getState().isAuthenticated()).toBe(true)
    })

    it('ユーザーが null の場合は false を返す', () => {
      useAuthStore.setState({ user: null })
      
      expect(useAuthStore.getState().isAuthenticated()).toBe(false)
    })
  })

  describe('統合テスト', () => {
    it('ログインフローのシミュレーション', () => {
      // 1. 初期状態（未認証）
      expect(useAuthStore.getState().isAuthenticated()).toBe(false)
      
      // 2. ユーザー情報を設定
      const user: UserResponse = {
        user_id: 'user-789',
        email: 'user@example.com',
        name: 'User Name',
      }
      useAuthStore.getState().setUser(user)
      expect(useAuthStore.getState().user).toEqual(user)
      expect(useAuthStore.getState().isAuthenticated()).toBe(true)
      
      // 3. ログアウト
      useAuthStore.getState().clearAuth()
      expect(useAuthStore.getState().isAuthenticated()).toBe(false)
      expect(useAuthStore.getState().user).toBeNull()
    })
  })
})
