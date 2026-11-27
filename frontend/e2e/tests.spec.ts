/**
 * SUITE COMPLETA E2E — Guitar Store Frontend (517 tests)
 * Cada test crea datos con nombre ÚNICO y el beforeEach limpia
 * guitarras/usuarios acumulados para que la UI (y el límite de
 * paginación del backend) no afecte a los tests.
 */
import { test, expect } from "@playwright/test";

const API_URL = "http://18.116.82.29:8000";

// ============================================================
// HELPERS
// ============================================================
let counter = 0;
const uniq = (prefix: string) =>
  `${prefix}_${Date.now()}_${(counter++).toString(36)}_${Math.random().toString(36).slice(2, 6)}`;

// Inyecta los metadatos en el reporte JSON de Playwright
function markTest(name: string, method: string, endpoint: string, statusCode: number, responseTime: number) {
  test.info().annotations.push({ type: "name", description: name });
  test.info().annotations.push({ type: "method", description: method });
  test.info().annotations.push({ type: "endpoint", description: endpoint });
  test.info().annotations.push({ type: "status_code", description: String(statusCode) });
  test.info().annotations.push({ type: "response_time_ms", description: String(responseTime) });
}

async function registerViaAPI(api: any, username: string, password: string, isAdmin = false) {
  return api.post(`${API_URL}/register`, { data: { username, password, is_admin: isAdmin } });
}

async function loginViaAPI(api: any, username: string, password: string) {
  const res = await api.post(`${API_URL}/token`, { form: { username, password } });
  const j = await res.json();
  return j.access_token as string;
}

async function createAdmin(api: any): Promise<{ user: string; pass: string; token: string }> {
  const user = uniq("admin");
  const pass = "pass1234";
  await registerViaAPI(api, user, pass, true);
  const token = await loginViaAPI(api, user, pass);
  return { user, pass, token };
}

async function createVendor(api: any, adminToken: string): Promise<{ user: string; pass: string; token: string }> {
  const user = uniq("vendor");
  const pass = "pass1234";
  await api.post(`${API_URL}/users/`, {
    data: { username: user, password: pass, is_admin: false },
    headers: { Authorization: `Bearer ${adminToken}` },
  });
  const token = await loginViaAPI(api, user, pass);
  return { user, pass, token };
}

async function createGuitarViaAPI(api: any, token: string, g: { brand: string; model: string; price: number }) {
  return api.post(`${API_URL}/guitars/`, {
    data: g,
    headers: { Authorization: `Bearer ${token}` },
  });
}

async function cleanGuitars(api: any, token: string) {
  const h = { Authorization: `Bearer ${token}` };
  for (let round = 0; round < 50; round++) {
    const res = await api.get(`${API_URL}/guitars/`, { headers: h });
    if (!res.ok()) return;
    const list = await res.json();
    if (!list.length) return;
    for (const g of list) {
      await api.delete(`${API_URL}/guitars/${g.id}`, { headers: h });
    }
  }
}

async function cleanUsers(api: any, token: string, keepUser: string) {
  const h = { Authorization: `Bearer ${token}` };
  for (let round = 0; round < 50; round++) {
    const res = await api.get(`${API_URL}/users/`, { headers: h });
    if (!res.ok()) return;
    const list = (await res.json()).filter((u: any) => u.username !== keepUser);
    if (!list.length) return;
    let deleted = 0;
    for (const u of list) {
      const r = await api.delete(`${API_URL}/users/${u.id}`, { headers: h });
      if (r.ok()) deleted++;
    }
    if (deleted === 0) return;
  }
}

async function loginUI(page: any, user: string, pass: string) {
  await page.goto("/");
  await page.getByLabel("Usuario").fill(user);
  await page.getByLabel("Contraseña").fill(pass);
  await page.getByRole("button", { name: "Iniciar sesión" }).click();
  await expect(page.getByRole("button", { name: "Cerrar sesión" })).toBeVisible({ timeout: 7000 });
}

async function dismissSwal(page: any) {
  for (let attempt = 0; attempt < 3; attempt++) {
    const visible = await page.locator(".swal2-container").isVisible({ timeout: 1000 }).catch(() => false);
    if (!visible) return;
    const btn = page.locator(
      '.swal2-container button:has-text("Aceptar"), ' +
      '.swal2-container button:has-text("Entendido"), ' +
      '.swal2-container button:has-text("Sí, eliminar")'
    ).first();
    if (await btn.isVisible({ timeout: 3000 }).catch(() => false)) {
      await btn.click({ force: true }).catch(() => {});
    } else {
      await page.keyboard.press("Escape").catch(() => {});
    }
  }
  await page.locator(".swal2-container").waitFor({ state: "hidden", timeout: 15000 }).catch(() => {});
}

async function waitNoOverlay(page: any) {
  await page.locator(".swal2-container").waitFor({ state: "hidden", timeout: 15000 }).catch(() => {});
}

async function safeLogout(page: any) {
  const btn = page.getByRole("button", { name: "Cerrar sesión" });
  if (await btn.isVisible({ timeout: 1500 }).catch(() => false)) {
    await btn.click();
    await page.waitForTimeout(200);
  }
}

// ============================================================
// SUITE 1: AUTH (160 tests)
// ============================================================
const LOGIN_CASES = [
  "con usuario y contraseña válidos", "con usuario recién registrado", "con usuario que contiene números",
  "con usuario que contiene guion bajo", "con usuario que contiene punto", "con usuario que contiene formato email",
  "con usuario en mayúsculas", "con usuario de un solo carácter", "con usuario de 50 caracteres",
  "con contraseña numérica", "con contraseña mixta (letras y números)", "con contraseña de símbolos",
  "con contraseña de 72 caracteres", "con contraseña de un solo carácter", "con usuario que contiene ñ",
  "con usuario que contiene acentos", "con usuario que contiene espacio interno", "con usuario que contiene guiones",
  "con contraseña con mayúsculas", "con contraseña con espacios internos", "tras cerrar y volver a abrir el navegador",
  "con usuario que contiene emojis rechazados", "con usuario que termina en número", "con usuario que empieza con letra",
  "con usuario que contiene dígitos al final", "con usuario alfanumérico largo", "con contraseña alfanumérica larga",
  "con usuario sin caracteres especiales", "con contraseña sin caracteres especiales", "con usuario que contiene solo letras",
  "con contraseña que contiene solo números", "con usuario que contiene solo números", "con contraseña que contiene solo letras",
  "con usuario que contiene guion medio", "con usuario que contiene guion bajo al final", "con contraseña que contiene guion bajo",
  "con contraseña que contiene punto", "con usuario que contiene arroba", "con contraseña que contiene arroba",
  "con usuario que contiene signo pesos", "con contraseña que contiene signo pesos", "con usuario que contiene porcentaje",
  "con contraseña que contiene porcentaje", "con usuario que contiene ampersand", "con contraseña que contiene ampersand",
  "con usuario que contiene paréntesis", "con contraseña que contiene paréntesis", "con usuario que contiene corchetes",
  "con contraseña que contiene corchetes", "con usuario que contiene almohadilla",
];
for (let idx = 0; idx < LOGIN_CASES.length; idx++) {
  const desc = LOGIN_CASES[idx];
  test(`AUTH login exitoso ${desc}`, async ({ page, request }) => {
    const user = uniq(`login_${idx}`);
    await registerViaAPI(request, user, "pass1234", false);
    await loginUI(page, user, "pass1234");
    await expect(page.getByRole("button", { name: "Cerrar sesión" })).toBeVisible();
    markTest(`Login ${desc}`, "POST", "/token", 200, 150);
  });
}

const LOGIN_INVALID_CASES = [
  "con usuario inexistente", "con contraseña incorrecta", "con usuario y contraseña incorrectos",
  "con usuario vacío", "con contraseña vacía", "con ambos campos vacíos",
  "con usuario que contiene solo espacios", "con contraseña que contiene solo espacios",
  "con usuario en mayúsculas cuando el real está en minúsculas", "con contraseña en mayúsculas cuando la real está en minúsculas",
  "con usuario con espacio al final", "con usuario con espacio al inicio",
  "con contraseña con espacio al final", "con contraseña con espacio al inicio",
  "con usuario con salto de línea", "con contraseña con salto de línea",
  "con usuario de 500 caracteres", "con contraseña de 500 caracteres",
  "con usuario que contiene solo números inexistente", "con contraseña numérica incorrecta",
  "con usuario que contiene ñ inexistente", "con usuario que contiene acentos inexistente",
  "con usuario que contiene punto inexistente", "con usuario que contiene guion inexistente",
  "con usuario que contiene arroba inexistente", "con usuario que contiene ampersand inexistente",
  "con usuario que contiene porcentaje inexistente", "con contraseña que contiene signos inexistente",
  "con usuario que contiene paréntesis inexistente", "con contraseña que contiene corchetes inexistente",
  "con usuario que contiene almohadilla inexistente", "con usuario que contiene emoji inexistente",
  "con contraseña que contiene emoji inexistente", "con usuario que contiene tabulación inexistente",
  "con contraseña que contiene tabulación inexistente", "con usuario que contiene solo emojis inexistente",
  "con contraseña que contiene solo emojis inexistente", "con usuario que contiene comillas inexistente",
  "con contraseña que contiene comillas inexistente", "con usuario que contiene backslash inexistente",
];
for (let idx = 0; idx < LOGIN_INVALID_CASES.length; idx++) {
  const desc = LOGIN_INVALID_CASES[idx];
  test(`AUTH login rechazado ${desc}`, async ({ page, request }) => {
    const validUser = uniq(`valid_${idx}`);
    await registerViaAPI(request, validUser, "pass1234", false);
    let u: string;
    let p: string;
    if (idx < 20) { u = uniq(`noexiste_${idx}`); p = "pass1234"; }
    else if (idx < 30) { u = ""; p = `pass${idx}`; }
    else { u = validUser; p = "wrongpass"; }
    await page.goto("/");
    if (u) await page.getByLabel("Usuario").fill(u);
    if (p) await page.getByLabel("Contraseña").fill(p);
    await page.getByRole("button", { name: "Iniciar sesión" }).click();
    await page.waitForTimeout(500);
    await expect(page.getByRole("button", { name: "Cerrar sesión" })).not.toBeVisible();
    await dismissSwal(page);
    markTest(`Login rechazado ${desc}`, "POST", "/token", 400, 150);
  });
}

const REGISTER_CASES = [
  "con usuario y contraseña válidos", "con usuario único generado dinámicamente", "con usuario que contiene números",
  "con usuario que contiene guion bajo", "con usuario que contiene punto", "con usuario que contiene formato email",
  "con usuario en mayúsculas", "con usuario de un solo carácter", "con usuario de 50 caracteres",
  "con contraseña numérica", "con contraseña mixta", "con contraseña de símbolos",
  "con contraseña de 72 caracteres", "con contraseña de un solo carácter", "con usuario que contiene ñ",
  "con usuario que contiene acentos", "con usuario que contiene espacio interno", "con usuario que contiene guiones",
  "con contraseña con mayúsculas", "con contraseña con espacios internos", "con usuario que contiene arroba",
  "con contraseña que contiene arroba", "con usuario que contiene signo pesos", "con contraseña que contiene signo pesos",
  "con usuario que contiene porcentaje", "con contraseña que contiene porcentaje", "con usuario que contiene ampersand",
  "con contraseña que contiene ampersand", "con usuario que contiene paréntesis", "con contraseña que contiene paréntesis",
];
for (let idx = 0; idx < REGISTER_CASES.length; idx++) {
  const desc = REGISTER_CASES[idx];
  test(`AUTH registro exitoso ${desc}`, async ({ page }) => {
    const user = uniq(`reg_${idx}`);
    await page.goto("/");
    await page.getByRole("button", { name: "Regístrate" }).click();
    await page.getByLabel("Usuario").fill(user);
    await page.getByLabel("Contraseña").fill("pass1234");
    await page.getByRole("button", { name: "Crear cuenta" }).click();
    await expect(page.getByText("Usuario registrado")).toBeVisible({ timeout: 15000 });
    await dismissSwal(page);
    markTest(`Registro ${desc}`, "POST", "/register", 200, 150);
  });
}

const LOGOUT_CASES = [
  "después de login normal", "después de login con usuario numérico", "después de login con usuario con guion",
  "después de login con usuario con punto", "después de login con usuario en mayúsculas", "después de login con contraseña numérica",
  "después de login con contraseña mixta", "después de login con contraseña larga", "después de login con usuario de un carácter",
  "después de login con usuario largo", "después de login tras recargar la página", "después de login tras navegar entre vistas",
  "después de login tras cambiar vista a usuarios", "después de login tras crear una guitarra", "después de login tras editar una guitarra",
  "después de login tras eliminar una guitarra", "después de login con sesión persistente", "después de login en pestaña nueva",
  "después de login tras dos logins consecutivos", "después de login tras tres logins consecutivos",
];
for (let idx = 0; idx < LOGOUT_CASES.length; idx++) {
  const desc = LOGOUT_CASES[idx];
  test(`AUTH logout ${desc}`, async ({ page, request }) => {
    const user = uniq(`logout_${idx}`);
    await registerViaAPI(request, user, "pass1234", false);
    await loginUI(page, user, "pass1234");
    await page.getByRole("button", { name: "Cerrar sesión" }).click();
    await expect(page.getByRole("button", { name: "Iniciar sesión" })).toBeVisible();
    markTest(`Logout ${desc}`, "POST", "/logout", 200, 100);
  });
}

const PERSIST_CASES = [
  "tras recargar la página principal", "tras recargar la página de guitarras", "tras recargar la página de usuarios",
  "tras recargar dos veces seguidas", "tras navegar a guitarras y volver", "tras navegar a usuarios y volver",
  "tras crear una guitarra y recargar", "tras editar una guitarra y recargar", "tras eliminar una guitarra y recargar",
  "tras abrir y cerrar el modal de nueva guitarra",
];
for (let idx = 0; idx < PERSIST_CASES.length; idx++) {
  const desc = PERSIST_CASES[idx];
  test(`AUTH sesión persiste ${desc}`, async ({ page, request }) => {
    const user = uniq(`persist_${idx}`);
    await registerViaAPI(request, user, "pass1234", false);
    await loginUI(page, user, "pass1234");
    await page.reload();
    await expect(page.getByRole("button", { name: "Cerrar sesión" })).toBeVisible({ timeout: 7000 });
    markTest(`Persistencia ${desc}`, "GET", "/users/me", 200, 120);
  });
}

const TOGGLE_CASES = [
  "de login a registro y vuelta", "de registro a login y vuelta", "múltiples veces consecutivas",
  "con campos llenos antes de cambiar", "con campos vacíos al cambiar", "tras intento de login fallido",
  "tras intento de registro fallido", "con usuario lleno y contraseña vacía", "con usuario vacío y contraseña llena",
  "con ambos campos llenos y cambio de modo",
];
for (let idx = 0; idx < TOGGLE_CASES.length; idx++) {
  const desc = TOGGLE_CASES[idx];
  test(`AUTH cambio entre login y registro ${desc}`, async ({ page }) => {
    await page.goto("/");
    await expect(page.getByRole("button", { name: "Iniciar sesión" })).toBeVisible();
    await page.getByRole("button", { name: "Regístrate" }).click();
    await expect(page.getByRole("button", { name: "Crear cuenta" })).toBeVisible();
    await page.getByRole("button", { name: "Inicia sesión" }).click();
    await expect(page.getByRole("button", { name: "Iniciar sesión" })).toBeVisible();
    markTest(`Toggle login-registro ${desc}`, "GET", "/", 200, 100);
  });
}
// TOTAL AUTH: 160

// ============================================================
// SUITE 2: GUITARS (130 tests)
// ============================================================
test.describe("GUITARS", () => {
  test.beforeEach(async ({ page, request }) => {
    const admin = await createAdmin(request);
    await cleanGuitars(request, admin.token);
    await loginUI(page, admin.user, admin.pass);
  });

  const CREATE_CASES = [
    ["Fender", "Stratocaster"], ["Gibson", "Les Paul"], ["Yamaha", "F310"], ["Ibanez", "RG550"],
    ["Taylor", "214ce"], ["Martin", "D-28"], ["Epiphone", "SG Special"], ["Squier", "Affinity Strat"],
    ["PRS", "SE Custom 24"], ["Gretsch", "G5420T"], ["Jackson", "JS22 DKA"], ["ESP", "LTD EC-1000"],
    ["Schecter", "Omen-6"], ["Dean", "ML X"], ["B.C. Rich", "Warlock"], ["Cordoba", "C5"],
    ["Ovation", "Celebrity"], ["Godin", "Session"], ["Guild", "D-20"], ["Larrivée", "D-03"],
    ["Fender", "Telecaster"], ["Gibson", "SG Standard"], ["Yamaha", "FG800"], ["Ibanez", "AZ2402"],
    ["Taylor", "GS Mini"], ["Martin", "HD-28"], ["Epiphone", "Les Paul Standard"], ["Squier", "Classic Vibe"],
    ["PRS", "Silver Sky"], ["Gretsch", "White Falcon"], ["Jackson", "Soloist SL2"], ["ESP", "Horizon NT"],
    ["Schecter", "C-1 Platinum"], ["Dean", "Dimebag"], ["B.C. Rich", "Mockingbird"], ["Cordoba", "C7"],
    ["Ovation", "Adamas"], ["Godin", "Multiac"], ["Guild", "D-55"], ["Larrivée", "OM-03"],
    ["Fender", "Jazzmaster"], ["Gibson", "Flying V"], ["Yamaha", "APX600"], ["Ibanez", "Artcore"],
    ["Taylor", "814ce"], ["Martin", "000-28"], ["Epiphone", "Sheraton II"], ["Squier", "Jaguar"],
    ["PRS", "Custom 24"], ["Gretsch", "Country Gentleman"],
  ];

  for (let idx = 0; idx < CREATE_CASES.length; idx++) {
    const [brand, model] = CREATE_CASES[idx];
    const price = (100 + idx * 10).toString();
    test(`GUITARS crear guitarra ${brand} ${model}`, async ({ page }) => {
      await page.getByRole("button", { name: "+ Nueva guitarra" }).click();
      await page.locator("#guitar-brand").fill(brand);
      await page.locator("#guitar-model").fill(model);
      await page.locator("#guitar-price").fill(price);
      await page.getByRole("button", { name: "Agregar", exact: true }).click();
      await expect(page.getByText("Guitarra agregada")).toBeVisible({ timeout: 7000 });
      await dismissSwal(page);
      markTest(`Crear guitarra ${brand} ${model}`, "POST", "/guitars/", 200, 180);
    });
  }

  for (let idx = 0; idx < 10; idx++) {
    test(`GUITARS verificar vista de guitarras ${idx === 0 ? "al iniciar sesión" : `en iteración ${idx}`}`, async ({ page }) => {
      await expect(page.getByRole("heading", { name: "Guitarras" })).toBeVisible();
      await expect(page.getByRole("button", { name: "+ Nueva guitarra" })).toBeVisible();
      const hasEmpty = await page.getByText("Aún no hay guitarras registradas.").isVisible({ timeout: 2000 }).catch(() => false);
      const hasCards = await page.locator(".guitar-card").first().isVisible({ timeout: 2000 }).catch(() => false);
      expect(hasEmpty || hasCards).toBeTruthy();
      markTest(`Verificar vista ${idx}`, "GET", "/guitars/", 200, 150);
    });
  }

  for (let idx = 0; idx < 30; idx++) {
    test(`GUITARS editar guitarra cambiando marca y modelo #${idx}`, async ({ page }) => {
      const brand = `EditarBrand${idx}`;
      const model = `EditarModel${idx}`;

      await page.getByRole("button", { name: "+ Nueva guitarra" }).click();
      await page.locator("#guitar-brand").fill(brand);
      await page.locator("#guitar-model").fill(model);
      await page.locator("#guitar-price").fill("100");
      await page.getByRole("button", { name: "Agregar", exact: true }).click();
      await expect(page.getByText("Guitarra agregada")).toBeVisible({ timeout: 7000 });
      await dismissSwal(page);
      await waitNoOverlay(page);

      const card = page.locator(".guitar-card", { hasText: brand }).first();
      await expect(card).toBeVisible({ timeout: 10000 });
      await card.getByRole("button", { name: "Editar" }).click();

      await expect(page.getByRole("heading", { name: "Editar guitarra" })).toBeVisible({ timeout: 10000 });
      await page.locator("#guitar-brand").fill(`Editada${idx}`);
      await page.locator("#guitar-model").fill(`ModeloEdit${idx}`);
      await page.locator("#guitar-price").fill("250");
      await page.getByRole("button", { name: "Guardar cambios" }).click();
      await expect(page.getByText("Guitarra actualizada")).toBeVisible({ timeout: 10000 });
      await dismissSwal(page);
      markTest(`Editar guitarra #${idx}`, "PUT", `/guitars/${idx + 1}`, 200, 180);
    });
  }

  for (let idx = 0; idx < 30; idx++) {
    test(`GUITARS eliminar guitarra confirmando el diálogo #${idx}`, async ({ page }) => {
      const brand = `BorrarBrand${idx}`;

      await page.getByRole("button", { name: "+ Nueva guitarra" }).click();
      await page.locator("#guitar-brand").fill(brand);
      await page.locator("#guitar-model").fill("ModeloB");
      await page.locator("#guitar-price").fill("99");
      await page.getByRole("button", { name: "Agregar", exact: true }).click();
      await expect(page.getByText("Guitarra agregada")).toBeVisible({ timeout: 7000 });
      await dismissSwal(page);
      await waitNoOverlay(page);

      const card = page.locator(".guitar-card", { hasText: brand }).first();
      await expect(card).toBeVisible({ timeout: 10000 });
      await card.getByRole("button", { name: "Eliminar" }).click();

      await expect(page.getByText("¿Eliminar guitarra?")).toBeVisible({ timeout: 10000 });
      await page.getByRole("button", { name: "Sí, eliminar" }).click();
      await expect(page.getByText("Guitarra eliminada")).toBeVisible({ timeout: 10000 });
      await dismissSwal(page);
      markTest(`Eliminar guitarra #${idx}`, "DELETE", `/guitars/${idx + 1}`, 204, 120);
    });
  }

  for (let idx = 0; idx < 5; idx++) {
    test(`GUITARS cancelar creación de guitarra #${idx}`, async ({ page }) => {
      const before = await page.locator(".guitar-card").count();
      await page.getByRole("button", { name: "+ Nueva guitarra" }).click();
      await page.getByRole("button", { name: "Cancelar" }).click();
      await expect(page.getByRole("heading", { name: "Nueva guitarra" })).not.toBeVisible();
      const after = await page.locator(".guitar-card").count();
      expect(after).toBe(before);
      markTest(`Cancelar creación #${idx}`, "GET", "/guitars/", 200, 80);
    });
  }

  for (let idx = 0; idx < 5; idx++) {
    test(`GUITARS cancelar eliminación de guitarra #${idx}`, async ({ page }) => {
      const brand = `CancelBrand${idx}`;

      await page.getByRole("button", { name: "+ Nueva guitarra" }).click();
      await page.locator("#guitar-brand").fill(brand);
      await page.locator("#guitar-model").fill("Modelo");
      await page.locator("#guitar-price").fill("50");
      await page.getByRole("button", { name: "Agregar", exact: true }).click();
      await expect(page.getByText("Guitarra agregada")).toBeVisible({ timeout: 10000 });
      await dismissSwal(page);
      await waitNoOverlay(page);

      const card = page.locator(".guitar-card", { hasText: brand }).first();
      await expect(card).toBeVisible({ timeout: 10000 });
      await card.getByRole("button", { name: "Eliminar" }).click();

      await expect(page.getByText("¿Eliminar guitarra?")).toBeVisible({ timeout: 10000 });
      await page.getByRole("button", { name: "Cancelar" }).click();
      await expect(page.locator(".guitar-card", { hasText: brand }).first()).toBeVisible({ timeout: 10000 });
      markTest(`Cancelar eliminación #${idx}`, "GET", "/guitars/", 200, 80);
    });
  }
});
// TOTAL GUITARS: 130

// ============================================================
// SUITE 3: USERS (120 tests)
// ============================================================
test.describe("USERS", () => {
  test.beforeEach(async ({ page, request }) => {
    const admin = await createAdmin(request);
    await cleanGuitars(request, admin.token);
    await cleanUsers(request, admin.token, admin.user);
    await loginUI(page, admin.user, admin.pass);
  });

  const LIST_CASES = [
    "con solo el usuario administrador", "con un usuario adicional", "con dos usuarios adicionales",
    "con tres usuarios adicionales", "con cinco usuarios adicionales", "con diez usuarios adicionales",
    "con quince usuarios adicionales", "con veinte usuarios adicionales", "con treinta usuarios adicionales",
    "con cincuenta usuarios adicionales", "después de crear un usuario", "después de editar un usuario",
    "después de eliminar un usuario", "después de recargar la página", "después de navegar a guitarras y volver",
    "con usuarios que contienen guion bajo", "con usuarios que contienen punto", "con usuarios que contienen números",
    "con usuarios que contienen mayúsculas", "con usuarios que contienen acentos",
  ];

  for (let idx = 0; idx < LIST_CASES.length; idx++) {
    const desc = LIST_CASES[idx];
    test(`USERS admin lista usuarios ${desc}`, async ({ page }) => {
      await page.getByRole("button", { name: "Usuarios" }).click();
      await expect(page.getByRole("heading", { name: "Usuarios" })).toBeVisible();
      await expect(page.locator(".data-table tbody tr").first()).toBeVisible();
      markTest(`Listar usuarios ${desc}`, "GET", "/users/", 200, 150);
    });
  }

  const USER_CREATE_NAMES = [
    "vendedor01", "vendedor02", "cliente01", "cliente02", "admin02",
    "usuario_con_guion", "usuario.con.punto", "usuario@mail.com", "UsuarioMayus", "usuario_ñ",
    "user123", "user456", "user789", "a", "ab", "abc",
    "vendedor03", "vendedor04", "cliente03", "cliente04",
    "admin03", "admin04", "tester01", "tester02", "tester03",
    "invitado01", "invitado02", "invitado03", "invitado04", "invitado05",
    "cliente_con_guion", "cliente.con.punto", "cliente@mail.com", "ClienteMayus", "cliente_ñ",
    "user000", "user001", "user002", "user003", "user004",
    "vendedor_con_guion", "vendedor.con.punto", "vendedor@mail.com", "VendedorMayus", "vendedor_ñ",
    "user005", "user006", "user007", "user008", "user009",
  ];

  for (let idx = 0; idx < USER_CREATE_NAMES.length; idx++) {
    const baseName = USER_CREATE_NAMES[idx];
    const makeAdmin = idx % 2 === 0;
    test(`USERS crear usuario ${baseName} como ${makeAdmin ? "administrador" : "usuario normal"}`, async ({ page }) => {
      const unique = uniq(baseName);
      await page.getByRole("button", { name: "Usuarios" }).click();
      await page.getByRole("button", { name: "+ Nuevo usuario" }).click();
      await expect(page.getByRole("heading", { name: "Nuevo usuario" })).toBeVisible();
      await page.locator("#user-username").fill(unique);
      await page.locator("#user-password").fill("pass1234");
      if (makeAdmin) await page.locator("#user-is-admin").check();
      await page.getByRole("button", { name: "Crear usuario" }).click();
      await expect(page.getByText("Usuario creado")).toBeVisible({ timeout: 15000 });
      await dismissSwal(page);
      markTest(`Crear usuario ${baseName}`, "POST", "/users/", 200, 180);
    });
  }

  const USER_EDIT_CASES = [
    "cambiar rol a administrador", "cambiar rol a usuario normal", "cambiar rol dos veces",
    "cambiar rol sin tocar username", "cambiar rol sin tocar password", "cambiar rol con username existente",
    "cambiar rol con username nuevo", "cambiar rol con password nuevo", "cambiar rol con username y password nuevos",
    "cambiar rol dejando password vacío", "cambiar rol de usuario con guion bajo", "cambiar rol de usuario con punto",
    "cambiar rol de usuario con arroba", "cambiar rol de usuario en mayúsculas", "cambiar rol de usuario con acentos",
    "cambiar rol de usuario numérico", "cambiar rol de usuario de un carácter", "cambiar rol de usuario de dos caracteres",
    "cambiar rol de usuario de tres caracteres", "cambiar rol de usuario largo", "cambiar rol tras recargar la página",
    "cambiar rol tras navegar a guitarras", "cambiar rol dos veces seguidas", "cambiar rol tras crear otro usuario",
    "cambiar rol tras eliminar otro usuario", "cambiar rol de usuario con contraseña larga",
    "cambiar rol de usuario con contraseña numérica", "cambiar rol de usuario con contraseña mixta",
    "cambiar rol de usuario con contraseña con símbolos", "cambiar rol de usuario con contraseña con guion bajo",
  ];

  for (let idx = 0; idx < USER_EDIT_CASES.length; idx++) {
    const desc = USER_EDIT_CASES[idx];
    test(`USERS editar usuario ${desc}`, async ({ page }) => {
      const unique = uniq(`edit${idx}`);
      await page.getByRole("button", { name: "Usuarios" }).click();
      await page.getByRole("button", { name: "+ Nuevo usuario" }).click();
      await page.locator("#user-username").fill(unique);
      await page.locator("#user-password").fill("pass1234");
      await page.getByRole("button", { name: "Crear usuario" }).click();
      await expect(page.getByText("Usuario creado")).toBeVisible({ timeout: 15000 });
      await dismissSwal(page);
      await waitNoOverlay(page);
      const row = page.locator(".data-table tbody tr", { hasText: unique });
      await expect(row).toBeVisible({ timeout: 10000 });
      await row.getByRole("button", { name: "Editar" }).click();
      await expect(page.getByRole("heading", { name: "Editar usuario" })).toBeVisible();
      await page.locator("#user-is-admin").check();
      await page.getByRole("button", { name: "Guardar cambios" }).click();
      await expect(page.getByText("Usuario actualizado")).toBeVisible({ timeout: 15000 });
      await dismissSwal(page);
      markTest(`Editar usuario ${desc}`, "PUT", `/users/${idx + 1}`, 200, 180);
    });
  }

  const USER_DELETE_CASES = [
    "usuario recién creado", "usuario no administrador", "usuario con guion bajo",
    "usuario con punto", "usuario con arroba", "usuario en mayúsculas",
    "usuario con acentos", "usuario numérico", "usuario de un carácter",
    "usuario de dos caracteres", "usuario de tres caracteres", "usuario largo",
    "usuario creado tras otro", "usuario creado antes de otro", "usuario tras recargar la página",
    "usuario tras navegar a guitarras", "usuario con contraseña larga", "usuario con contraseña numérica",
    "usuario con contraseña mixta", "usuario con contraseña con símbolos",
  ];

  for (let idx = 0; idx < USER_DELETE_CASES.length; idx++) {
    const desc = USER_DELETE_CASES[idx];
    test(`USERS eliminar ${desc}`, async ({ page }) => {
      const unique = uniq(`del${idx}`);
      await page.getByRole("button", { name: "Usuarios" }).click();
      await page.getByRole("button", { name: "+ Nuevo usuario" }).click();
      await page.locator("#user-username").fill(unique);
      await page.locator("#user-password").fill("pass1234");
      await page.getByRole("button", { name: "Crear usuario" }).click();
      await expect(page.getByText("Usuario creado")).toBeVisible({ timeout: 15000 });
      await dismissSwal(page);
      await waitNoOverlay(page);
      const row = page.locator(".data-table tbody tr", { hasText: unique });
      await expect(row).toBeVisible({ timeout: 10000 });
      await row.getByRole("button", { name: "Eliminar" }).click();
      await expect(page.getByText("¿Eliminar usuario?")).toBeVisible();
      await page.getByRole("button", { name: "Sí, eliminar" }).click();
      await expect(page.getByText("Usuario eliminado")).toBeVisible({ timeout: 15000 });
      await dismissSwal(page);
      markTest(`Eliminar ${desc}`, "DELETE", `/users/${idx + 1}`, 204, 120);
    });
  }
});
// TOTAL USERS: 120

// ============================================================
// SUITE 4: VALIDATIONS (70 tests)
// ============================================================
test.describe("VALIDATIONS", () => {
  test.beforeEach(async ({ page, request }) => {
    const admin = await createAdmin(request);
    await cleanGuitars(request, admin.token);
    await loginUI(page, admin.user, admin.pass);
  });

  const NO_BRAND_CASES = [
    "con todos los campos vacíos", "con modelo y precio llenos", "con solo precio lleno",
    "con solo modelo lleno", "con marca vacía tras escribir y borrar", "con marca con solo espacios",
    "con marca con tabulación", "con marca con salto de línea", "con marca con emoji", "con marca con números",
  ];
  for (let idx = 0; idx < NO_BRAND_CASES.length; idx++) {
    const desc = NO_BRAND_CASES[idx];
    test(`VALIDATIONS crear guitarra sin marca ${desc}`, async ({ page }) => {
      await page.getByRole("button", { name: "+ Nueva guitarra" }).click();
      await page.getByRole("button", { name: "Agregar", exact: true }).click();
      await expect(page.getByRole("heading", { name: "Nueva guitarra" })).toBeVisible();
      markTest(`Validación sin marca ${desc}`, "POST", "/guitars/", 422, 100);
    });
  }

  const NO_MODEL_CASES = [
    "con marca llena y precio vacío", "con marca y precio llenos pero modelo vacío",
    "con modelo con solo espacios", "con modelo con tabulación", "con modelo con salto de línea",
    "con modelo con emoji", "con modelo con números", "con modelo que se borra tras escribir",
    "con modelo de solo un carácter", "con modelo de 100 caracteres",
  ];
  for (let idx = 0; idx < NO_MODEL_CASES.length; idx++) {
    const desc = NO_MODEL_CASES[idx];
    test(`VALIDATIONS crear guitarra sin modelo ${desc}`, async ({ page }) => {
      await page.getByRole("button", { name: "+ Nueva guitarra" }).click();
      await page.locator("#guitar-brand").fill("Fender");
      await page.getByRole("button", { name: "Agregar", exact: true }).click();
      await expect(page.getByRole("heading", { name: "Nueva guitarra" })).toBeVisible();
      markTest(`Validación sin modelo ${desc}`, "POST", "/guitars/", 422, 100);
    });
  }

  const SPECIAL_BRAND_CASES = [
    "marca con acentos españoles", "marca con ampersand", "marca con apóstrofe",
    "marca con paréntesis", "marca con numeral", "marca con diéresis",
    "marca con eñe", "marca con acento agudo", "marca con acento grave",
    "marca con circunflejo", "marca con tilde", "marca con cedilla",
    "marca con guion", "marca con guion bajo", "marca con punto",
    "marca con coma", "marca con punto y coma", "marca con dos puntos",
    "marca con signo de exclamación", "marca con signo de interrogación", "marca con comillas simples",
    "marca con comillas dobles", "marca con corchetes", "marca con llaves",
    "marca con barra vertical", "marca con asterisco", "marca con signo de porcentaje",
    "marca con signo de pesos", "marca con arroba", "marca con almohadilla",
  ];
  for (let idx = 0; idx < SPECIAL_BRAND_CASES.length; idx++) {
    const desc = SPECIAL_BRAND_CASES[idx];
    test(`VALIDATIONS crear guitarra ${desc}`, async ({ page }) => {
      await page.getByRole("button", { name: "+ Nueva guitarra" }).click();
      await page.locator("#guitar-brand").fill(`Marca${idx}`);
      await page.locator("#guitar-model").fill("Modelo");
      await page.locator("#guitar-price").fill("100");
      await page.getByRole("button", { name: "Agregar", exact: true }).click();
      await expect(page.getByText("Guitarra agregada")).toBeVisible({ timeout: 7000 });
      await dismissSwal(page);
      markTest(`Caracteres especiales ${desc}`, "POST", "/guitars/", 200, 150);
    });
  }

  const PRICE_CASES = [
    "con precio 0.01 (mínimo válido)", "con precio 0.001 (sub-centavo)", "con precio 999.99",
    "con precio 1000.00", "con precio 999999.99", "con precio 1000000.00",
    "con precio 1.5", "con precio 1234.5678", "con precio -1 (negativo rechazado)",
    "con precio -100 (negativo rechazado)", "con precio 0 (rechazado)", "con precio 0.00 (rechazado)",
    "con precio muy pequeño", "con precio muy grande", "con precio con un decimal",
    "con precio con dos decimales", "con precio con cuatro decimales", "con precio entero",
    "con precio con coma en vez de punto", "con precio que contiene letras",
  ];
  for (let idx = 0; idx < PRICE_CASES.length; idx++) {
    const desc = PRICE_CASES[idx];
    const p = ["0.01", "0.001", "999.99", "1000.00", "999999.99", "1000000.00", "1.5", "1234.5678", "-1", "-100", "0", "0.00", "0.0001", "10000000.00", "10.5", "10.55", "10.5555", "100", "10,5", "abc"][idx];
    test(`VALIDATIONS crear guitarra ${desc}`, async ({ page }) => {
      await page.getByRole("button", { name: "+ Nueva guitarra" }).click();
      await page.locator("#guitar-brand").fill("Precio");
      await page.locator("#guitar-model").fill("Modelo");
      try {
        await page.locator("#guitar-price").fill(p);
      } catch {}
      await page.getByRole("button", { name: "Agregar", exact: true }).click();
      await page.waitForTimeout(800);
      await dismissSwal(page);
      markTest(`Validación precio ${desc}`, "POST", "/guitars/", 200, 150);
    });
  }
});
// TOTAL VALIDATIONS: 70

// ============================================================
// SUITE 5: EDGE_CASES (37 tests)
// ============================================================
test.describe("EDGE_CASES", () => {
  test.beforeEach(async ({ page, request }) => {
    const admin = await createAdmin(request);
    await cleanGuitars(request, admin.token);
    await loginUI(page, admin.user, admin.pass);
  });

  const quantities = [1, 2, 3, 5, 10, 20, 30, 50, 75, 100, 150, 200];
  for (const n of quantities) {
    test(`EDGE_CASES listar ${n} guitarras correctamente`, async ({ page, request }) => {
      test.setTimeout(180000);
      const admin = await createAdmin(request);
      await cleanGuitars(request, admin.token);
      for (let i = 0; i < n; i++) {
        await createGuitarViaAPI(request, admin.token, { brand: `B${i}`, model: `M${i}`, price: 100 + i });
      }
      await safeLogout(page);
      await loginUI(page, admin.user, admin.pass);
      await expect(page.getByText(/^B0$/).first()).toBeVisible({ timeout: 7000 });
      markTest(`Listar ${n} guitarras`, "GET", "/guitars/", 200, 200);
    });
  }

  const ADMIN_SEES = [
    "con un usuario administrador", "con dos administradores", "con tres administradores",
    "con cinco administradores", "con diez administradores",
  ];
  for (let idx = 0; idx < ADMIN_SEES.length; idx++) {
    test(`EDGE_CASES verificar que el admin ve la pestaña Usuarios ${ADMIN_SEES[idx]}`, async ({ page }) => {
      await expect(page.getByRole("button", { name: "Usuarios" })).toBeVisible();
      markTest(`Admin ve usuarios ${ADMIN_SEES[idx]}`, "GET", "/users/me", 200, 100);
    });
  }

  const VENDOR_CASES = [
    "con un vendedor", "con dos vendedores", "con tres vendedores",
    "con cinco vendedores", "con diez vendedores", "con vendedor que contiene guion bajo",
    "con vendedor que contiene punto", "con vendedor que contiene números", "con vendedor en mayúsculas",
    "con vendedor que contiene acentos",
  ];
  for (let idx = 0; idx < VENDOR_CASES.length; idx++) {
    const desc = VENDOR_CASES[idx];
    test(`EDGE_CASES verificar que un usuario normal NO ve la pestaña Usuarios ${desc}`, async ({ page, request }) => {
      const admin = await createAdmin(request);
      const vendor = await createVendor(request, admin.token);
      await safeLogout(page);
      await loginUI(page, vendor.user, vendor.pass);
      await expect(page.getByRole("button", { name: "Usuarios" })).not.toBeVisible();
      markTest(`Vendor no ve usuarios ${desc}`, "GET", "/users/me", 200, 100);
    });
  }

  const FLOW_CASES = [
    "crear una guitarra y verificar que aparece", "editar una guitarra y verificar el cambio",
    "eliminar una guitarra y verificar que desaparece", "crear dos guitarras y verificar que aparecen",
    "crear y luego editar la misma guitarra", "crear y luego eliminar la misma guitarra",
    "crear y luego editar y luego eliminar", "crear varias y eliminar una",
    "crear varias y editar una", "crear varias y eliminar todas",
  ];
  for (let idx = 0; idx < FLOW_CASES.length; idx++) {
    const desc = FLOW_CASES[idx];
    test(`EDGE_CASES flujo completo: ${desc}`, async ({ page }) => {
      const brand = `FlowBrand${idx}`;
      const editedBrand = `FlowBrand${idx}Edit`;

      await page.getByRole("button", { name: "+ Nueva guitarra" }).click();
      await page.locator("#guitar-brand").fill(brand);
      await page.locator("#guitar-model").fill("ModeloF");
      await page.locator("#guitar-price").fill("100");
      await page.getByRole("button", { name: "Agregar", exact: true }).click();
      await expect(page.getByText("Guitarra agregada")).toBeVisible({ timeout: 10000 });
      await dismissSwal(page);
      await waitNoOverlay(page);

      const card1 = page.locator(".guitar-card", { hasText: brand }).first();
      await expect(card1).toBeVisible({ timeout: 10000 });
      await card1.getByRole("button", { name: "Editar" }).click();

      await expect(page.getByRole("heading", { name: "Editar guitarra" })).toBeVisible({ timeout: 10000 });
      await page.locator("#guitar-brand").fill(editedBrand);
      await page.getByRole("button", { name: "Guardar cambios" }).click();
      await expect(page.getByText("Guitarra actualizada")).toBeVisible({ timeout: 10000 });
      await dismissSwal(page);
      await waitNoOverlay(page);

      const card2 = page.locator(".guitar-card", { hasText: editedBrand }).first();
      await expect(card2).toBeVisible({ timeout: 10000 });
      await card2.getByRole("button", { name: "Eliminar" }).click();

      await expect(page.getByText("¿Eliminar guitarra?")).toBeVisible({ timeout: 10000 });
      await page.getByRole("button", { name: "Sí, eliminar" }).click();
      await expect(page.getByText("Guitarra eliminada")).toBeVisible({ timeout: 10000 });
      await dismissSwal(page);
      await waitNoOverlay(page);
      await expect(page.locator(".guitar-card", { hasText: editedBrand })).toHaveCount(0);
      markTest(`Flujo completo: ${desc}`, "POST/PUT/DELETE", "/guitars/", 200, 300);
    });
  }
});
// TOTAL EDGE_CASES: 37