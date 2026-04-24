const KEY = "ranger.adminToken";

export function getAdminToken(): string | null {
  return localStorage.getItem(KEY);
}

export function setAdminToken(token: string): void {
  localStorage.setItem(KEY, token);
}

export function clearAdminToken(): void {
  localStorage.removeItem(KEY);
}
