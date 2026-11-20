import api from '@/api/client'
import type { User, TokenResponse } from '@/types'

export const authService = {
  async login(username: string, password: string): Promise<TokenResponse> {
    const form = new URLSearchParams()
    form.append('username', username)
    form.append('password', password)
    const { data } = await api.post<TokenResponse>('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return data
  },

  async getMe(): Promise<User> {
    const { data } = await api.get<User>('/auth/me')
    return data
  },

  async changePassword(oldPassword: string, newPassword: string): Promise<{ message: string }> {
    const { data } = await api.post<{ message: string }>('/auth/change-password', null, {
      params: { old_password: oldPassword, new_password: newPassword },
    })
    return data
  },
}
