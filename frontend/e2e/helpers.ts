import { Page, APIRequestContext, request } from "@playwright/test";

export const API_URL = "http://127.0.0.1:8000";

export interface TestResult {
  event: string;
  suite: string;
  test_name: string;
  description: string;
  status: "passed" | "failed" | "skipped";
  duration_ms: number;
  timestamp: string;
  commit_sha: string;
  branch: string;
  actor: string;
  input: unknown;
  expected: unknown;
  method: string;
  endpoint: string;
  status_code: number | null;
  response_time_ms: number | null;
  error_message: string | null;
}

/**
 * Crea un usuario admin único usando la API (más rápido que por UI).
 * Devuelve { username, password, token }.
 */
export async function createAdminViaAPI(
  api: APIRequestContext,
  username: string,
  password: string,
): Promise<{ username: string; password: string; token: string }> {
  // Registrar (el primero es admin automáticamente)
  await api.post(`${API_URL}/register`, {
    data: { username, password, is_admin: false },
  });
  // Login
  const tokenRes = await api.post(`${API_URL}/token`, {
    form: { username, password },
  });
  const { access_token } = await tokenRes.json();
  return { username, password, token: access_token };
}

/**
 * Hace login por UI y espera a que cargue la vista de guitarras.
 */
export async function loginUI(page: Page, username: string, password: string) {
  await page.goto("/");
  await page.getByLabel("Usuario").fill(username);
  await page.getByLabel("Contraseña").fill(password);
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  // Espera a que aparezca el sidebar con el username
  await page
    .getByText("Guitarras", { exact: false })
    .first()
    .waitFor({ timeout: 7000 });
}

/**
 * Ejecuta una acción y devuelve el tiempo en ms (aproximado por Playwright).
 */
export async function timed<T>(
  fn: () => Promise<T>,
): Promise<{ result: T; ms: number }> {
  const start = Date.now();
  const result = await fn();
  return { result, ms: Date.now() - start };
}
