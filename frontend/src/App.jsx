import { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";
import { alertSuccess, alertError, confirmDialog } from "./alerts";

const API_URL = "http://3.145.207.146:8000/";

function App() {
  const [token, setToken] = useState(localStorage.getItem("token") || "");
  const [currentUser, setCurrentUser] = useState(null);
  const [view, setView] = useState("guitars");

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isRegistering, setIsRegistering] = useState(false);

  const [guitars, setGuitars] = useState([]);
  const [showGuitarModal, setShowGuitarModal] = useState(false);
  const [editingGuitarId, setEditingGuitarId] = useState(null);
  const [guitarForm, setGuitarForm] = useState({
    brand: "",
    model: "",
    price: "",
  });

  const [users, setUsers] = useState([]);
  const [showUserModal, setShowUserModal] = useState(false);
  const [editingUserId, setEditingUserId] = useState(null);
  const [userForm, setUserForm] = useState({
    username: "",
    password: "",
    is_admin: false,
  });

  useEffect(() => {
    if (token) {
      axios
        .get(`${API_URL}/users/me`, {
          headers: { Authorization: `Bearer ${token}` },
        })
        .then((res) => setCurrentUser(res.data))
        .catch(() => handleLogout());
    }
  }, [token]);

  useEffect(() => {
    if (token && currentUser) {
      fetchGuitars();
      if (currentUser.is_admin) fetchUsers();
    }
  }, [token, currentUser, view]);

  // ---------- AUTH ----------
  const handleLogin = async (e) => {
    e.preventDefault();
    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);
    try {
      const res = await axios.post(`${API_URL}/token`, formData);
      setToken(res.data.access_token);
      localStorage.setItem("token", res.data.access_token);
      setUsername("");
      setPassword("");
    } catch {
      await alertError("Usuario o contraseña incorrectos");
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API_URL}/register`, { username, password });
      setIsRegistering(false);
      setUsername("");
      setPassword("");
      await alertSuccess("Usuario registrado", "Ahora puedes iniciar sesión");
    } catch (error) {
      await alertError(
        "Error al registrar",
        error.response?.data?.detail || "Intenta de nuevo",
      );
    }
  };

  const handleLogout = () => {
    setToken("");
    setCurrentUser(null);
    setGuitars([]);
    setUsers([]);
    localStorage.removeItem("token");
  };

  // ---------- GUITARRAS ----------
  const fetchGuitars = async () => {
    try {
      const res = await axios.get(`${API_URL}/guitars/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setGuitars(res.data);
    } catch {
      /* ignore */
    }
  };

  const openNewGuitar = () => {
    setEditingGuitarId(null);
    setGuitarForm({ brand: "", model: "", price: "" });
    setShowGuitarModal(true);
  };

  const openEditGuitar = (g) => {
    setEditingGuitarId(g.id);
    setGuitarForm({ brand: g.brand, model: g.model, price: g.price });
    setShowGuitarModal(true);
  };

  const submitGuitar = async (e) => {
    e.preventDefault();
    try {
      // Convertir price a número (el backend lo requiere estricto)
      const payload = {
        brand: guitarForm.brand,
        model: guitarForm.model,
        price: parseFloat(guitarForm.price),
      };
      if (editingGuitarId) {
        await axios.put(`${API_URL}/guitars/${editingGuitarId}`, payload, {
          headers: { Authorization: `Bearer ${token}` },
        });
      } else {
        await axios.post(`${API_URL}/guitars/`, payload, {
          headers: { Authorization: `Bearer ${token}` },
        });
      }
      setShowGuitarModal(false);
      await fetchGuitars();
      await alertSuccess(
        editingGuitarId ? "Guitarra actualizada" : "Guitarra agregada",
      );
    } catch (err) {
      const detail = err.response?.data?.detail;
      await alertError(
        "No se pudo guardar",
        typeof detail === "string"
          ? detail
          : JSON.stringify(detail) || "Revisa los datos e intenta de nuevo",
      );
    }
  };

  const deleteGuitar = async (id) => {
    const r = await confirmDialog(
      "¿Eliminar guitarra?",
      "Esta acción no se puede deshacer.",
    );
    if (!r.isConfirmed) return;
    try {
      await axios.delete(`${API_URL}/guitars/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      await fetchGuitars();
      await alertSuccess("Guitarra eliminada");
    } catch {
      await alertError("No se pudo eliminar");
    }
  };

  // ---------- USUARIOS ----------
  const fetchUsers = async () => {
    try {
      const res = await axios.get(`${API_URL}/users/`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setUsers(res.data);
    } catch {
      /* ignore */
    }
  };

  const openNewUser = () => {
    setEditingUserId(null);
    setUserForm({ username: "", password: "", is_admin: false });
    setShowUserModal(true);
  };

  const openEditUser = (u) => {
    setEditingUserId(u.id);
    setUserForm({ username: u.username, password: "", is_admin: u.is_admin });
    setShowUserModal(true);
  };

  const submitUser = async (e) => {
    e.preventDefault();
    try {
      if (editingUserId) {
        const payload = { is_admin: userForm.is_admin };
        if (userForm.username) payload.username = userForm.username;
        if (userForm.password) payload.password = userForm.password;
        await axios.put(`${API_URL}/users/${editingUserId}`, payload, {
          headers: { Authorization: `Bearer ${token}` },
        });
      } else {
        await axios.post(`${API_URL}/users/`, userForm, {
          headers: { Authorization: `Bearer ${token}` },
        });
      }
      setShowUserModal(false);
      await fetchUsers();
      await alertSuccess(
        editingUserId ? "Usuario actualizado" : "Usuario creado",
      );
    } catch (error) {
      await alertError(
        "Error al guardar",
        error.response?.data?.detail || "Intenta de nuevo",
      );
    }
  };

  const deleteUser = async (id) => {
    const r = await confirmDialog(
      "¿Eliminar usuario?",
      "Esta acción no se puede deshacer.",
    );
    if (!r.isConfirmed) return;
    try {
      await axios.delete(`${API_URL}/users/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      await fetchUsers();
      await alertSuccess("Usuario eliminado");
    } catch (error) {
      await alertError(
        "No se pudo eliminar",
        error.response?.data?.detail || "Intenta de nuevo",
      );
    }
  };

  // ---------- LOGIN VIEW ----------
  if (!token) {
    return (
      <div className="auth-wrapper">
        <div className="auth-card">
          <div className="auth-brand">
            <div className="brand-mark">G</div>
            <h1>Guitar Store</h1>
          </div>
          <p className="auth-subtitle">
            {isRegistering
              ? "Crea tu cuenta para comenzar"
              : "Bienvenido de nuevo"}
          </p>
          <form onSubmit={isRegistering ? handleRegister : handleLogin}>
            <div className="field">
              <label htmlFor="login-username">Usuario</label>
              <input
                id="login-username"
                name="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>
            <div className="field">
              <label htmlFor="login-password">Contraseña</label>
              <input
                id="login-password"
                name="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
            <button type="submit" className="btn-primary">
              {isRegistering ? "Crear cuenta" : "Iniciar sesión"}
            </button>
          </form>
          <p className="auth-switch">
            {isRegistering ? "¿Ya tienes cuenta?" : "¿No tienes cuenta?"}{" "}
            <button
              className="link-btn"
              onClick={() => setIsRegistering(!isRegistering)}
            >
              {isRegistering ? "Inicia sesión" : "Regístrate"}
            </button>
          </p>
        </div>
      </div>
    );
  }

  // ---------- APP ----------
  return (
    <div className="app-layout">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="brand-mark small">G</div>
          <span>Guitar Store</span>
        </div>
        <nav>
          <button
            className={view === "guitars" ? "nav-active" : ""}
            onClick={() => setView("guitars")}
          >
            Guitarras
          </button>
          {currentUser?.is_admin && (
            <button
              className={view === "users" ? "nav-active" : ""}
              onClick={() => setView("users")}
            >
              Usuarios
            </button>
          )}
        </nav>
        <div className="sidebar-footer">
          <div className="user-badge">
            <div className="avatar">
              {currentUser?.username?.[0]?.toUpperCase()}
            </div>
            <div>
              <div className="user-name">{currentUser?.username}</div>
              <div className="user-role">
                {currentUser?.is_admin ? "Administrador" : "Usuario"}
              </div>
            </div>
          </div>
          <button className="btn-logout" onClick={handleLogout}>
            Cerrar sesión
          </button>
        </div>
      </aside>

      <main className="main-content">
        {view === "guitars" && (
          <>
            <header className="page-header">
              <div>
                <h1>Guitarras</h1>
                <p>Gestiona tu catálogo de guitarras</p>
              </div>
              <button className="btn-primary" onClick={openNewGuitar}>
                + Nueva guitarra
              </button>
            </header>

            {guitars.length === 0 ? (
              <div className="empty-state">
                <p>Aún no hay guitarras registradas.</p>
                <button className="btn-primary" onClick={openNewGuitar}>
                  Agregar la primera
                </button>
              </div>
            ) : (
              <div className="guitar-grid">
                {guitars.map((g) => (
                  <div key={g.id} className="guitar-card">
                    <div className="guitar-image">♪</div>
                    <h3>{g.brand}</h3>
                    <p className="guitar-model">{g.model}</p>
                    <p className="guitar-price">${g.price.toFixed(2)}</p>
                    <div className="guitar-actions">
                      <button
                        className="btn-edit"
                        onClick={() => openEditGuitar(g)}
                      >
                        Editar
                      </button>
                      <button
                        className="btn-danger"
                        onClick={() => deleteGuitar(g.id)}
                      >
                        Eliminar
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}

        {view === "users" && currentUser?.is_admin && (
          <>
            <header className="page-header">
              <div>
                <h1>Usuarios</h1>
                <p>Administra los usuarios del sistema</p>
              </div>
              <button className="btn-primary" onClick={openNewUser}>
                + Nuevo usuario
              </button>
            </header>

            <div className="card">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Usuario</th>
                    <th>Rol</th>
                    <th>Acciones</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id}>
                      <td>{u.id}</td>
                      <td>{u.username}</td>
                      <td>
                        <span
                          className={`badge ${u.is_admin ? "badge-admin" : "badge-user"}`}
                        >
                          {u.is_admin ? "Administrador" : "Usuario"}
                        </span>
                      </td>
                      <td>
                        <button
                          className="btn-edit"
                          onClick={() => openEditUser(u)}
                        >
                          Editar
                        </button>
                        <button
                          className="btn-danger"
                          onClick={() => deleteUser(u.id)}
                        >
                          Eliminar
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </main>

      {showGuitarModal && (
        <div
          className="modal-overlay"
          onClick={() => setShowGuitarModal(false)}
        >
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{editingGuitarId ? "Editar guitarra" : "Nueva guitarra"}</h2>
            <form onSubmit={submitGuitar}>
              <div className="field">
                <label htmlFor="guitar-brand">Marca</label>
                <input
                  id="guitar-brand"
                  name="brand"
                  value={guitarForm.brand}
                  onChange={(e) =>
                    setGuitarForm({ ...guitarForm, brand: e.target.value })
                  }
                  required
                />
              </div>
              <div className="field">
                <label htmlFor="guitar-model">Modelo</label>
                <input
                  id="guitar-model"
                  name="model"
                  value={guitarForm.model}
                  onChange={(e) =>
                    setGuitarForm({ ...guitarForm, model: e.target.value })
                  }
                  required
                />
              </div>
              <div className="field">
                <label htmlFor="guitar-price">Precio</label>
                <input
                  id="guitar-price"
                  name="price"
                  type="number"
                  step="0.01"
                  value={guitarForm.price}
                  onChange={(e) =>
                    setGuitarForm({ ...guitarForm, price: e.target.value })
                  }
                  required
                />
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-ghost"
                  onClick={() => setShowGuitarModal(false)}
                >
                  Cancelar
                </button>
                <button type="submit" className="btn-primary">
                  {editingGuitarId ? "Guardar cambios" : "Agregar"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {showUserModal && (
        <div className="modal-overlay" onClick={() => setShowUserModal(false)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <h2>{editingUserId ? "Editar usuario" : "Nuevo usuario"}</h2>
            <form onSubmit={submitUser}>
              <div className="field">
                <label htmlFor="user-username">Usuario</label>
                <input
                  id="user-username"
                  name="username"
                  value={userForm.username}
                  onChange={(e) =>
                    setUserForm({ ...userForm, username: e.target.value })
                  }
                  required={!editingUserId}
                />
              </div>
              <div className="field">
                <label htmlFor="user-password">
                  {editingUserId ? "Nueva contraseña (opcional)" : "Contraseña"}
                </label>
                <input
                  id="user-password"
                  name="password"
                  type="password"
                  value={userForm.password}
                  onChange={(e) =>
                    setUserForm({ ...userForm, password: e.target.value })
                  }
                  required={!editingUserId}
                />
              </div>
              <div className="field checkbox">
                <label htmlFor="user-is-admin">
                  <input
                    id="user-is-admin"
                    name="is_admin"
                    type="checkbox"
                    checked={userForm.is_admin}
                    onChange={(e) =>
                      setUserForm({ ...userForm, is_admin: e.target.checked })
                    }
                  />
                  <span>Es administrador</span>
                </label>
              </div>
              <div className="modal-actions">
                <button
                  type="button"
                  className="btn-ghost"
                  onClick={() => setShowUserModal(false)}
                >
                  Cancelar
                </button>
                <button type="submit" className="btn-primary">
                  {editingUserId ? "Guardar cambios" : "Crear usuario"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
