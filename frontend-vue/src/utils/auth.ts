import Cookies from 'js-cookie'

const TOKEN_KEY = 'lawsker_token'
const TOKEN_EXPIRES = 7 // 7天

export function getToken(): string | undefined {
  return Cookies.get(TOKEN_KEY)
}

export function setToken(token: string): void {
  Cookies.set(TOKEN_KEY, token, { expires: TOKEN_EXPIRES, secure: true, sameSite: 'strict' })
}

export function removeToken(): void {
  Cookies.remove(TOKEN_KEY)
}

export function hasToken(): boolean {
  return !!getToken()
}