const TOKEN_KEY = 'dealerToken';
const EXPIRES_KEY = 'dealerTokenExpiresAt';

export function saveSession(token, expiresInSeconds) {
  sessionStorage.setItem(TOKEN_KEY, token);
  sessionStorage.setItem(EXPIRES_KEY, String(Date.now() + expiresInSeconds * 1000));
}

export function getToken() {
  const expiresAt = Number(sessionStorage.getItem(EXPIRES_KEY));
  if (!expiresAt || expiresAt <= Date.now()) {
    clearSession();
    return null;
  }
  return sessionStorage.getItem(TOKEN_KEY);
}

export const isAuthenticated = () => Boolean(getToken());

export function clearSession() {
  sessionStorage.removeItem(TOKEN_KEY);
  sessionStorage.removeItem(EXPIRES_KEY);
}
