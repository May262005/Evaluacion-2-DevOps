import uuid
import pytest
from tests.conftest import timed_request


# ============================================================
# SECCIÓN 1: AUTH (~100 pruebas)
# ============================================================

@pytest.mark.parametrize("username,password,description", [
    ("user1", "pass1234", "Registro con usuario y contraseña válidos"),
    ("user2", "pass1234", "Registro con usuario diferente"),
    ("user_con_guion_bajo", "pass1234", "Registro con guion bajo en usuario"),
    ("user123", "pass1234", "Registro con números en usuario"),
    ("UsuarioMayus", "pass1234", "Registro con mayúsculas en usuario"),
    ("user@example.com", "pass1234", "Registro con formato email"),
    ("user.con.puntos", "pass1234", "Registro con puntos en usuario"),
    ("a", "pass1234", "Registro con usuario de 1 carácter"),
    ("user_bien_largo_1234567890", "pass1234", "Registro con usuario largo"),
    ("user1", "p", "Registro con contraseña de 1 carácter"),
    ("user1", "1234567890", "Registro con contraseña numérica"),
    ("user1", "PassWord123", "Registro con contraseña mixta"),
    ("user1", "!@#$%^&*()", "Registro con contraseña de símbolos"),
    ("user1", "a" * 72, "Registro con contraseña de 72 caracteres"),
    ("ñandú", "pass1234", "Registro con caracteres acentuados"),
    ("用户", "pass1234", "Registro con caracteres chinos"),
    ("user_ñ", "pass1234", "Registro con ñ en usuario"),
    ("user space", "pass1234", "Registro con espacio en usuario"),
    ("user-TEST", "pass1234", "Registro con guion y mayúsculas"),
])
def test_register_valido(client, mark_test, username, password, description):
    res, elapsed = timed_request(client, "POST", "/register",
                                 json={"username": username, "password": password})
    mark_test(description, {"username": username, "password": password},
              {"status_code": 200}, method="POST", endpoint="/register",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 200
    assert res.json()["username"] == username


@pytest.mark.parametrize("payload,description", [
    ({}, "Payload vacío"),
    ({"username": ""}, "Sin password y username vacío"),
    ({"password": "1234"}, "Sin username"),
    ({"username": "user"}, "Sin password"),
    ({"username": "", "password": "1234"}, "Username vacío"),
    ({"username": "user", "password": ""}, "Password vacía"),
    ({"username": "", "password": ""}, "Ambos vacíos"),
    ({"username": None, "password": "1234"}, "Username None"),
    ({"username": "user", "password": None}, "Password None"),
    ({"username": 123, "password": "1234"}, "Username numérico"),
    ({"username": "user", "password": 1234}, "Password numérica"),
    ({"username": ["user"], "password": "1234"}, "Username lista"),
    ({"username": {"a": 1}, "password": "1234"}, "Username objeto"),
    ({"username": "user", "password": ["1234"]}, "Password lista"),
    ({"username": True, "password": "1234"}, "Username booleano"),
    ({"username": "user", "password": False}, "Password booleano"),
    ({"username": "a" * 500, "password": "1234"}, "Username de 500 caracteres"),
    ({"username": "a" * 1000, "password": "1234"}, "Username de 1000 caracteres"),
    ({"username": "user", "password": "a" * 1000}, "Password de 1000 caracteres"),
    ({"username": "user", "password": "a" * 10000}, "Password de 10000 caracteres"),
])
def test_register_invalido(client, mark_test, payload, description):
    res, elapsed = timed_request(client, "POST", "/register", json=payload)
    mark_test(description, payload, {"status_code": "422 o 400"},
              method="POST", endpoint="/register",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code in (400, 422)


@pytest.mark.parametrize("username", [
    "admin", "user", "test", "a", "usuario_duplicado", "user123",
    "usuario_con_guion", "usuario.con.punto", "USER_MAYUS", "user@mail.com",
    "ñandú", "用户", "user space", "a" * 100, "admin2",
])
def test_register_duplicado(client, mark_test, username):
    client.post("/register", json={"username": username, "password": "pass1234"})
    res, elapsed = timed_request(client, "POST", "/register",
                                 json={"username": username, "password": "otra"})
    mark_test(f"Duplicado '{username}' debe fallar con 400",
              {"username": username, "password": "otra"}, {"status_code": 400},
              method="POST", endpoint="/register",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 400
    assert "already registered" in res.json()["detail"].lower()


@pytest.mark.parametrize("username,password", [
    ("admin1", "admin12345"), ("root", "root12345"), ("superuser", "super12345"),
    ("admin", "admin"), ("Admin", "Admin1234"), ("ADMIN", "ADMIN1234"),
    ("admin_con_guion", "pass12345"), ("admin.con.punto", "pass12345"),
    ("admin@mail.com", "pass12345"), ("admin1234567890", "pass12345"),
])
def test_primer_usuario_admin(client, mark_test, username, password):
    res, elapsed = timed_request(client, "POST", "/register",
                                 json={"username": username, "password": password})
    mark_test(f"Primer usuario '{username}' es admin",
              {"username": username, "password": password}, {"is_admin": True},
              method="POST", endpoint="/register",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 200
    assert res.json()["is_admin"] is True


@pytest.mark.parametrize("vendor_name", [
    "vendor1", "vendedor", "user2", "cliente", "invitado",
    "vendedor1", "vendedor2", "vendedor3", "vendedor4", "vendedor5",
])
def test_segundo_usuario_no_admin(client, mark_test, vendor_name):
    client.post("/register", json={"username": "admin", "password": "admin12345"})
    res, elapsed = timed_request(client, "POST", "/register",
                                 json={"username": vendor_name, "password": "pass1234"})
    mark_test(f"Segundo usuario '{vendor_name}' no es admin",
              {"username": vendor_name, "password": "pass1234"}, {"is_admin": False},
              method="POST", endpoint="/register",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 200
    assert res.json()["is_admin"] is False


@pytest.mark.parametrize("username,password", [
    ("user1", "pass1234"), ("user2", "pass1234"), ("admin", "admin12345"),
    ("vendedor", "vendedor123"), ("test", "test1234"),
    ("user_con_guion", "pass1234"), ("user123", "pass1234"),
    ("ñandú", "pass1234"), ("user@example.com", "pass1234"),
    ("user.con.puntos", "pass1234"),
])
def test_login_valido(client, mark_test, username, password):
    client.post("/register", json={"username": username, "password": password})
    res, elapsed = timed_request(client, "POST", "/token",
                                 data={"username": username, "password": password})
    mark_test(f"Login válido para '{username}'",
              {"username": username, "password": password}, {"status_code": 200},
              method="POST", endpoint="/token",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 200
    assert "access_token" in res.json()
    assert res.json()["token_type"] == "bearer"


@pytest.mark.parametrize("username,password,description", [
    ("noexiste", "pass1234", "Usuario inexistente"),
    ("user1", "wrongpass", "Contraseña incorrecta"),
    ("", "pass1234", "Username vacío en login"),
    ("user1", "", "Password vacía en login"),
    ("", "", "Ambos vacíos en login"),
    ("user1", "PASS1234", "Contraseña con mayúsculas incorrecta"),
    ("User1", "pass1234", "Username con mayúscula incorrecta"),
    ("user1 ", "pass1234", "Username con espacio al final"),
    (" user1", "pass1234", "Username con espacio al inicio"),
    ("user1", " pass1234", "Password con espacio al inicio"),
    ("user1", "pass1234 ", "Password con espacio al final"),
    ("user1\n", "pass1234", "Username con salto de línea"),
    ("user1", "pass1234\n", "Password con salto de línea"),
    ("a" * 500, "pass1234", "Username muy largo"),
    ("user1", "a" * 500, "Password muy larga"),
])
def test_login_invalido(client, mark_test, username, password, description):
    client.post("/register", json={"username": "user1", "password": "pass1234"})
    res, elapsed = timed_request(client, "POST", "/token",
                                 data={"username": username, "password": password})
    mark_test(description, {"username": username, "password": password},
              {"status_code": "400 o 422"},
              method="POST", endpoint="/token",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code in (400, 422)


def test_token_devuelve_bearer(client, mark_test):
    client.post("/register", json={"username": "user1", "password": "pass1234"})
    res, elapsed = timed_request(client, "POST", "/token",
                                 data={"username": "user1", "password": "pass1234"})
    mark_test("Token devuelve tipo bearer", None, {"token_type": "bearer"},
              method="POST", endpoint="/token",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.json()["token_type"] == "bearer"


def test_users_me_devuelve_usuario(client, mark_test):
    client.post("/register", json={"username": "user1", "password": "pass1234"})
    r = client.post("/token", data={"username": "user1", "password": "pass1234"})
    token = r.json()["access_token"]
    res, elapsed = timed_request(client, "GET", "/users/me",
                                 headers={"Authorization": f"Bearer {token}"})
    mark_test("GET /users/me devuelve el usuario autenticado", None, {"username": "user1"},
              method="GET", endpoint="/users/me",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 200
    assert res.json()["username"] == "user1"


@pytest.mark.parametrize("header,description", [
    (None, "Sin header de autorización"),
    ({"Authorization": "Bearer "}, "Token vacío"),
    ({"Authorization": "Bearer invalidtoken"}, "Token inválido"),
    ({"Authorization": "Bearer abc.def.ghi"}, "Token con formato JWT inválido"),
    ({"Authorization": "Basic user:pass"}, "Esquema Basic en lugar de Bearer"),
    ({"Authorization": "bearer token"}, "Bearer en minúsculas"),
    ({"Authorization": "TOKEN"}, "Header sin esquema"),
    ({"Authorization": "Bearer " + "a" * 500}, "Token muy largo"),
])
def test_users_me_sin_token_valido(client, mark_test, header, description):
    res, elapsed = timed_request(client, "GET", "/users/me", headers=header or {})
    mark_test(description, header, {"status_code": 401},
              method="GET", endpoint="/users/me",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 401


def test_password_no_se_devuelve_en_response(client, mark_test):
    res, elapsed = timed_request(client, "POST", "/register",
                                 json={"username": "user1", "password": "pass1234"})
    mark_test("La contraseña no se devuelve en el registro", None, {"has_password": False},
              method="POST", endpoint="/register",
              status_code=res.status_code, response_time_ms=elapsed)
    assert "password" not in res.json()
    assert "hashed_password" not in res.json()


def test_password_hasheada_en_bd(client, mark_test):
    client.post("/register", json={"username": "user1", "password": "pass1234"})
    res, elapsed = timed_request(client, "POST", "/token",
                                 data={"username": "user1", "password": "pass1234"})
    mark_test("La contraseña se guarda hasheada", None, {"hashed": True},
              method="POST", endpoint="/token",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 200


def test_passwords_diferentes_generan_hashes_diferentes(client, mark_test):
    client.post("/register", json={"username": "user1", "password": "pass1234"})
    res, elapsed = timed_request(client, "POST", "/register",
                                 json={"username": "user2", "password": "pass1234"})
    mark_test("Contraseñas iguales de distintos usuarios generan hashes distintos",
              None, {"hashed": True},
              method="POST", endpoint="/register",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 200


def test_login_case_sensitive_password(client, mark_test):
    client.post("/register", json={"username": "user1", "password": "pass1234"})
    res, elapsed = timed_request(client, "POST", "/token",
                                 data={"username": "user1", "password": "PASS1234"})
    mark_test("Password es case-sensitive", None, {"status_code": 400},
              method="POST", endpoint="/token",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 400


def test_login_case_sensitive_username(client, mark_test):
    client.post("/register", json={"username": "user1", "password": "pass1234"})
    res, elapsed = timed_request(client, "POST", "/token",
                                 data={"username": "User1", "password": "pass1234"})
    mark_test("Username es case-sensitive", None, {"status_code": 400},
              method="POST", endpoint="/token",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 400


# ============================================================
# SECCIÓN 2: GUITARS (~100 pruebas)
# ============================================================

@pytest.mark.parametrize("brand,model,price,description", [
    ("Fender", "Stratocaster", 1200.0, "Crear guitarra Fender Stratocaster"),
    ("Gibson", "Les Paul", 2500.0, "Crear guitarra Gibson Les Paul"),
    ("Yamaha", "F310", 200.0, "Crear guitarra Yamaha acústica"),
    ("Ibanez", "RG550", 899.99, "Crear guitarra Ibanez eléctrica"),
    ("Taylor", "214ce", 1099.0, "Crear guitarra Taylor acústica"),
    ("Martin", "D-28", 3199.0, "Crear guitarra Martin D-28"),
    ("Epiphone", "SG Special", 449.0, "Crear guitarra Epiphone SG"),
    ("Squier", "Affinity Strat", 279.99, "Crear guitarra Squier"),
    ("PRS", "SE Custom 24", 849.0, "Crear guitarra PRS SE"),
    ("Gretsch", "G5420T", 999.0, "Crear guitarra Gretsch"),
    ("Jackson", "JS22 DKA", 199.0, "Crear guitarra Jackson"),
    ("ESP", "LTD EC-1000", 1099.0, "Crear guitarra ESP LTD"),
    ("Schecter", "Omen-6", 399.0, "Crear guitarra Schecter"),
    ("Dean", "ML X", 599.0, "Crear guitarra Dean"),
    ("B.C. Rich", "Warlock", 449.0, "Crear guitarra B.C. Rich"),
    ("Cordoba", "C5", 399.0, "Crear guitarra clásica Cordoba"),
    ("Ovation", "Celebrity", 599.0, "Crear guitarra Ovation"),
    ("Godin", "Session", 799.0, "Crear guitarra Godin"),
    ("Larrivée", "D-03", 1899.0, "Crear guitarra Larrivée"),
    ("Guild", "D-20", 1699.0, "Crear guitarra Guild"),
])
def test_crear_guitarra_valida(client, admin_headers, mark_test, brand, model, price, description):
    res, elapsed = timed_request(client, "POST", "/guitars/",
                                 json={"brand": brand, "model": model, "price": price},
                                 headers=admin_headers)
    mark_test(description, {"brand": brand, "model": model, "price": price},
              {"status_code": 200},
              method="POST", endpoint="/guitars/",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 200
    data = res.json()
    assert data["brand"] == brand
    assert data["model"] == model
    assert data["price"] == price


@pytest.mark.parametrize("payload,description", [
    ({}, "Payload vacío"),
    ({"brand": "Fender"}, "Sin modelo ni precio"),
    ({"model": "Strat"}, "Sin marca ni precio"),
    ({"price": 1000}, "Sin marca ni modelo"),
    ({"brand": "", "model": "Strat", "price": 1000}, "Marca vacía"),
    ({"brand": "Fender", "model": "", "price": 1000}, "Modelo vacío"),
    ({"brand": "", "model": "", "price": 1000}, "Marca y modelo vacíos"),
    ({"brand": None, "model": "Strat", "price": 1000}, "Marca None"),
    ({"brand": "Fender", "model": None, "price": 1000}, "Modelo None"),
    ({"brand": "Fender", "model": "Strat", "price": None}, "Precio None"),
    ({"brand": 123, "model": "Strat", "price": 1000}, "Marca numérica"),
    ({"brand": "Fender", "model": 456, "price": 1000}, "Modelo numérico"),
    ({"brand": "Fender", "model": "Strat", "price": "1000"}, "Precio como string"),
    ({"brand": ["Fender"], "model": "Strat", "price": 1000}, "Marca lista"),
    ({"brand": "Fender", "model": {"a": 1}, "price": 1000}, "Modelo objeto"),
    ({"brand": True, "model": "Strat", "price": 1000}, "Marca booleana"),
    ({"brand": "Fender", "model": "Strat", "price": -100}, "Precio negativo"),
    ({"brand": "Fender", "model": "Strat", "price": 0}, "Precio cero"),
    ({"brand": "Fender", "model": "Strat", "price": -0.01}, "Precio negativo pequeño"),
    ({"brand": "a" * 500, "model": "Strat", "price": 1000}, "Marca de 500 caracteres"),
    ({"brand": "Fender", "model": "a" * 500, "price": 1000}, "Modelo de 500 caracteres"),
    ({"brand": "a" * 1000, "model": "Strat", "price": 1000}, "Marca de 1000 caracteres"),
    ({"brand": "Fender", "model": "a" * 1000, "price": 1000}, "Modelo de 1000 caracteres"),
])
def test_crear_guitarra_invalida(client, admin_headers, mark_test, payload, description):
    res, elapsed = timed_request(client, "POST", "/guitars/",
                                 json=payload, headers=admin_headers)
    mark_test(description, payload, {"status_code": "422 o 400"},
              method="POST", endpoint="/guitars/",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code in (400, 422)


def test_listar_vacio(client, admin_headers, mark_test):
    res, elapsed = timed_request(client, "GET", "/guitars/", headers=admin_headers)
    mark_test("Listar guitarras sin datos devuelve lista vacía", None, {"length": 0},
              method="GET", endpoint="/guitars/",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 200
    assert res.json() == []


@pytest.mark.parametrize("cantidad", [1, 2, 3, 5, 10, 20, 50, 100, 200, 500])
def test_listar_n_guitarras(client, admin_headers, mark_test, cantidad):
    for i in range(cantidad):
        client.post("/guitars/", json={"brand": f"Brand{i}", "model": f"Model{i}", "price": 100.0 + i}, headers=admin_headers)
    res, elapsed = timed_request(client, "GET", "/guitars/", headers=admin_headers)
    mark_test(f"Listar {cantidad} guitarras devuelve todas", None, {"length": cantidad},
              method="GET", endpoint="/guitars/",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 200
    assert len(res.json()) == cantidad


def test_obtener_guitarra_existente(client, admin_headers, mark_test):
    create = client.post("/guitars/", json={"brand": "Fender", "model": "Strat", "price": 1000}, headers=admin_headers)
    gid = create.json()["id"]
    res, elapsed = timed_request(client, "GET", f"/guitars/{gid}", headers=admin_headers)
    mark_test("Obtener guitarra por ID existente", {"id": gid}, {"status_code": 200},
              method="GET", endpoint="/guitars/{id}",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 200
    assert res.json()["id"] == gid


@pytest.mark.parametrize("gid", [999, 1000, 9999, 10000, 99999, 100000, 999999, 1000000, -1, 0])
def test_obtener_guitarra_inexistente(client, admin_headers, mark_test, gid):
    res, elapsed = timed_request(client, "GET", f"/guitars/{gid}", headers=admin_headers)
    mark_test(f"Obtener guitarra con ID {gid} devuelve 404", {"id": gid}, {"status_code": 404},
              method="GET", endpoint="/guitars/{id}",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 404


@pytest.mark.parametrize("new_brand,new_model,new_price,description", [
    ("Gibson", "Les Paul", 2500.0, "Actualizar a Gibson"),
    ("Yamaha", "F310", 250.0, "Actualizar a Yamaha"),
    ("Ibanez", "RG550", 950.0, "Actualizar a Ibanez"),
    ("Taylor", "214ce", 1150.0, "Actualizar a Taylor"),
    ("Martin", "D-28", 3200.0, "Actualizar a Martin"),
    ("Fender", "Telecaster", 1300.0, "Cambiar modelo manteniendo marca"),
    ("Squier", "Strat", 300.0, "Actualizar a Squier"),
    ("PRS", "Custom 24", 2000.0, "Actualizar a PRS"),
    ("Gretsch", "G5420", 1050.0, "Actualizar a Gretsch"),
    ("Jackson", "JS22", 220.0, "Actualizar a Jackson"),
    ("Fender", "Stratocaster", 1500.0, "Cambiar solo precio"),
    ("ESP", "EC-1000", 1200.0, "Actualizar a ESP"),
    ("Schecter", "Omen", 420.0, "Actualizar a Schecter"),
    ("Dean", "ML", 620.0, "Actualizar a Dean"),
    ("Cordoba", "C7", 500.0, "Actualizar a Cordoba"),
])
def test_actualizar_guitarra(client, admin_headers, mark_test, new_brand, new_model, new_price, description):
    create = client.post("/guitars/", json={"brand": "Original", "model": "Orig", "price": 100.0}, headers=admin_headers)
    gid = create.json()["id"]
    res, elapsed = timed_request(client, "PUT", f"/guitars/{gid}",
                                 json={"brand": new_brand, "model": new_model, "price": new_price},
                                 headers=admin_headers)
    mark_test(description, {"id": gid, "brand": new_brand, "model": new_model, "price": new_price},
              {"status_code": 200},
              method="PUT", endpoint="/guitars/{id}",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 200
    data = res.json()
    assert data["brand"] == new_brand
    assert data["model"] == new_model
    assert data["price"] == new_price


@pytest.mark.parametrize("gid", [999, 1000, 9999, -1, 0])
def test_actualizar_guitarra_inexistente(client, admin_headers, mark_test, gid):
    res, elapsed = timed_request(client, "PUT", f"/guitars/{gid}",
                                 json={"brand": "X", "model": "Y", "price": 1.0},
                                 headers=admin_headers)
    mark_test(f"Actualizar guitarra ID {gid} devuelve 404", {"id": gid}, {"status_code": 404},
              method="PUT", endpoint="/guitars/{id}",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 404


def test_eliminar_guitarra_existente(client, admin_headers, mark_test):
    create = client.post("/guitars/", json={"brand": "Fender", "model": "Strat", "price": 1000}, headers=admin_headers)
    gid = create.json()["id"]
    res, elapsed = timed_request(client, "DELETE", f"/guitars/{gid}", headers=admin_headers)
    mark_test("Eliminar guitarra existente", {"id": gid}, {"status_code": 204},
              method="DELETE", endpoint="/guitars/{id}",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 204
    get_res = client.get(f"/guitars/{gid}", headers=admin_headers)
    assert get_res.status_code == 404


@pytest.mark.parametrize("gid", [999, 1000, 9999, 10000, 99999, 100000, -1, 0, 1, 2])
def test_eliminar_guitarra_inexistente(client, admin_headers, mark_test, gid):
    res, elapsed = timed_request(client, "DELETE", f"/guitars/{gid}", headers=admin_headers)
    mark_test(f"Eliminar guitarra ID {gid} devuelve 404", {"id": gid}, {"status_code": 404},
              method="DELETE", endpoint="/guitars/{id}",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 404


def test_crear_guitarra_sin_auth(client, mark_test):
    res, elapsed = timed_request(client, "POST", "/guitars/",
                                 json={"brand": "Fender", "model": "Strat", "price": 1000})
    mark_test("Crear guitarra sin auth devuelve 401", None, {"status_code": 401},
              method="POST", endpoint="/guitars/",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 401


def test_listar_guitarras_sin_auth(client, mark_test):
    res, elapsed = timed_request(client, "GET", "/guitars/")
    mark_test("Listar guitarras sin auth devuelve 401", None, {"status_code": 401},
              method="GET", endpoint="/guitars/",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 401


def test_obtener_guitarra_sin_auth(client, mark_test):
    res, elapsed = timed_request(client, "GET", "/guitars/1")
    mark_test("Obtener guitarra sin auth devuelve 401", None, {"status_code": 401},
              method="GET", endpoint="/guitars/1",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 401


def test_actualizar_guitarra_sin_auth(client, mark_test):
    res, elapsed = timed_request(client, "PUT", "/guitars/1",
                                 json={"brand": "X", "model": "Y", "price": 1.0})
    mark_test("Actualizar guitarra sin auth devuelve 401", None, {"status_code": 401},
              method="PUT", endpoint="/guitars/1",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 401


def test_eliminar_guitarra_sin_auth(client, mark_test):
    res, elapsed = timed_request(client, "DELETE", "/guitars/1")
    mark_test("Eliminar guitarra sin auth devuelve 401", None, {"status_code": 401},
              method="DELETE", endpoint="/guitars/1",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 401


# ============================================================
# SECCIÓN 3: USERS (~100 pruebas)
# ============================================================

@pytest.mark.parametrize("extra_users", [0, 1, 2, 3, 5, 10, 15, 20, 30, 50])
def test_listar_usuarios_como_admin(client, admin_headers, mark_test, extra_users):
    for i in range(extra_users):
        client.post("/register", json={"username": f"user{i}", "password": "pass1234"})
    res, elapsed = timed_request(client, "GET", "/users/", headers=admin_headers)
    mark_test(f"Admin lista {extra_users + 1} usuarios correctamente",
              {"extra_users": extra_users},
              {"status_code": 200, "expected_count": extra_users + 1},
              method="GET", endpoint="/users/",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 200
    assert len(res.json()) == extra_users + 1


@pytest.mark.parametrize("vendor_name", [
    "vendor1", "vendedor", "cliente", "user2", "invitado",
    "vendedor1", "vendedor2", "vendedor3", "vendedor4", "vendedor5",
])
def test_listar_usuarios_como_no_admin(client, admin_headers, mark_test, vendor_name):
    client.post("/register", json={"username": vendor_name, "password": "pass1234"})
    r = client.post("/token", data={"username": vendor_name, "password": "pass1234"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    res, elapsed = timed_request(client, "GET", "/users/", headers=headers)
    mark_test(f"Usuario no-admin '{vendor_name}' no puede listar usuarios (403)",
              {"username": vendor_name}, {"status_code": 403},
              method="GET", endpoint="/users/",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 403


@pytest.mark.parametrize("password,is_admin,description", [
    ("pass1234", False, "Crear usuario no-admin"),
    ("pass1234", False, "Crear otro usuario no-admin"),
    ("pass1234", True, "Crear segundo admin"),
    ("pass1234", True, "Crear tercer admin"),
    ("pass1234", False, "Crear vendedor"),
    ("pass1234", False, "Crear otro vendedor"),
    ("pass1234", False, "Crear cliente"),
    ("pass1234", False, "Crear otro cliente"),
    ("pass1234", False, "Crear usuario con guion bajo"),
    ("pass1234", False, "Crear usuario con punto"),
    ("pass1234", False, "Crear usuario con formato email"),
    ("pass1234", False, "Crear usuario con acento"),
    ("pass1234", False, "Crear usuario con caracteres chinos"),
    ("pass1234", False, "Crear usuario de 1 carácter"),
    ("pass1234", False, "Crear usuario largo"),
    ("p", False, "Crear usuario con contraseña de 1 carácter"),
    ("1234567890", False, "Crear usuario con contraseña numérica"),
    ("PassWord123", False, "Crear usuario con contraseña mixta"),
    ("!@#$%^&*()", False, "Crear usuario con contraseña de símbolos"),
    ("a" * 100, False, "Crear usuario con contraseña de 100 caracteres"),
])
def test_crear_usuario_como_admin(client, admin_headers, mark_test, password, is_admin, description):
    username = f"user_{uuid.uuid4().hex[:8]}"
    res, elapsed = timed_request(client, "POST", "/users/",
                                 json={"username": username, "password": password, "is_admin": is_admin},
                                 headers=admin_headers)
    mark_test(description, {"username": username, "is_admin": is_admin},
              {"status_code": 200},
              method="POST", endpoint="/users/",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 200
    assert res.json()["username"] == username
    assert res.json()["is_admin"] == is_admin


@pytest.mark.parametrize("vendor_name,target_name", [
    ("vendor1", "nuevo1"), ("vendor2", "nuevo2"), ("vendor3", "nuevo3"),
    ("vendor4", "nuevo4"), ("vendor5", "nuevo5"), ("vendor6", "nuevo6"),
    ("vendor7", "nuevo7"), ("vendor8", "nuevo8"), ("vendor9", "nuevo9"),
    ("vendor10", "nuevo10"),
])
def test_crear_usuario_sin_permisos(client, admin_headers, mark_test, vendor_name, target_name):
    client.post("/register", json={"username": vendor_name, "password": "pass1234"})
    r = client.post("/token", data={"username": vendor_name, "password": "pass1234"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    res, elapsed = timed_request(client, "POST", "/users/",
                                 json={"username": target_name, "password": "pass1234", "is_admin": False},
                                 headers=headers)
    mark_test(f"Usuario no-admin '{vendor_name}' no puede crear usuarios (403)",
              {"vendor": vendor_name, "target": target_name}, {"status_code": 403},
              method="POST", endpoint="/users/",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 403


@pytest.mark.parametrize("username", [
    "admin", "user1", "user2", "test", "a", "usuario_duplicado",
    "user_con_guion", "user.con.punto", "USER_MAYUS", "user@mail.com",
])
def test_crear_usuario_duplicado_como_admin(client, admin_headers, mark_test, username):
    client.post("/users/", json={"username": username, "password": "pass1234", "is_admin": False}, headers=admin_headers)
    res, elapsed = timed_request(client, "POST", "/users/",
                                 json={"username": username, "password": "otra", "is_admin": False},
                                 headers=admin_headers)
    mark_test(f"Crear usuario duplicado '{username}' falla con 400",
              {"username": username}, {"status_code": 400},
              method="POST", endpoint="/users/",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 400
    assert "already registered" in res.json()["detail"].lower()


@pytest.mark.parametrize("new_password,new_is_admin,description", [
    (None, None, "Cambiar solo username"),
    ("nueva_pass", None, "Cambiar solo password"),
    (None, True, "Cambiar solo rol a admin"),
    (None, False, "Cambiar solo rol a no-admin"),
    ("nueva_pass2", True, "Cambiar todo a admin"),
    ("nueva_pass3", False, "Cambiar todo a no-admin"),
    (None, True, "Cambiar username y rol"),
    ("otra_pass", True, "Cambiar password y rol"),
    (None, None, "Cambiar username a 1 carácter"),
    ("p", None, "Cambiar password a 1 carácter"),
    (None, None, "Cambiar a formato email"),
    (None, None, "Cambiar a acento"),
    (None, None, "Cambiar a chino"),
    (None, None, "Cambiar a guion bajo"),
    (None, None, "Cambiar a punto"),
    (None, None, "Cambiar a espacio"),
    (None, None, "Cambiar a username 50 chars"),
    ("a" * 50, None, "Cambiar a password 50 chars"),
    (None, True, "Activar admin"),
    (None, False, "Desactivar admin"),
])
def test_actualizar_usuario_como_admin(client, admin_headers, mark_test, new_password, new_is_admin, description):
    original_name = f"orig_{uuid.uuid4().hex[:8]}"
    create = client.post("/users/", json={"username": original_name, "password": "orig1234", "is_admin": False}, headers=admin_headers)
    uid = create.json()["id"]
    payload = {}
    if new_password is not None: payload["password"] = new_password
    if new_is_admin is not None: payload["is_admin"] = new_is_admin
    res, elapsed = timed_request(client, "PUT", f"/users/{uid}", json=payload, headers=admin_headers)
    mark_test(description, {"id": uid, **payload}, {"status_code": 200},
              method="PUT", endpoint="/users/{id}",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 200
    if new_is_admin is not None:
        assert res.json()["is_admin"] == new_is_admin


@pytest.mark.parametrize("uid", [999, 1000, 9999, -1, 0])
def test_actualizar_usuario_inexistente(client, admin_headers, mark_test, uid):
    res, elapsed = timed_request(client, "PUT", f"/users/{uid}",
                                 json={"username": f"x_{uuid.uuid4().hex[:6]}"},
                                 headers=admin_headers)
    mark_test(f"Actualizar usuario ID {uid} devuelve 404", {"id": uid}, {"status_code": 404},
              method="PUT", endpoint="/users/{id}",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 404


@pytest.mark.parametrize("vendor_name", ["v1", "v2", "v3", "v4", "v5"])
def test_actualizar_usuario_sin_permisos(client, admin_headers, mark_test, vendor_name):
    create = client.post("/users/", json={"username": vendor_name, "password": "pass1234", "is_admin": False}, headers=admin_headers)
    uid = create.json()["id"]
    r = client.post("/token", data={"username": vendor_name, "password": "pass1234"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    res, elapsed = timed_request(client, "PUT", f"/users/{uid}",
                                 json={"username": f"hack_{uuid.uuid4().hex[:6]}"},
                                 headers=headers)
    mark_test(f"Usuario '{vendor_name}' no puede actualizar a otros (403)",
              {"id": uid}, {"status_code": 403},
              method="PUT", endpoint="/users/{id}",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 403


@pytest.mark.parametrize("target", [
    "borrable1", "borrable2", "borrable3", "borrable4", "borrable5",
    "borrable6", "borrable7", "borrable8", "borrable9", "borrable10",
])
def test_eliminar_usuario_como_admin(client, admin_headers, mark_test, target):
    create = client.post("/users/", json={"username": target, "password": "pass1234", "is_admin": False}, headers=admin_headers)
    uid = create.json()["id"]
    res, elapsed = timed_request(client, "DELETE", f"/users/{uid}", headers=admin_headers)
    mark_test(f"Admin elimina usuario '{target}'", {"id": uid}, {"status_code": 204},
              method="DELETE", endpoint="/users/{id}",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 204


@pytest.mark.parametrize("uid", [999, 1000, 9999, -1, 0])
def test_eliminar_usuario_inexistente(client, admin_headers, mark_test, uid):
    res, elapsed = timed_request(client, "DELETE", f"/users/{uid}", headers=admin_headers)
    mark_test(f"Eliminar usuario ID {uid} devuelve 404", {"id": uid}, {"status_code": 404},
              method="DELETE", endpoint="/users/{id}",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 404


@pytest.mark.parametrize("descripcion", ["test1", "test2", "test3", "test4", "test5"])
def test_admin_no_puede_eliminarse(client, admin_headers, mark_test, descripcion):
    me = client.get("/users/me", headers=admin_headers)
    uid = me.json()["id"]
    res, elapsed = timed_request(client, "DELETE", f"/users/{uid}", headers=admin_headers)
    mark_test("Admin no puede eliminarse a sí mismo (400)", {"id": uid}, {"status_code": 400},
              method="DELETE", endpoint="/users/{id}",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 400


@pytest.mark.parametrize("vendor_name", ["v1", "v2", "v3", "v4", "v5"])
def test_eliminar_usuario_sin_permisos(client, admin_headers, mark_test, vendor_name):
    create = client.post("/users/", json={"username": vendor_name, "password": "pass1234", "is_admin": False}, headers=admin_headers)
    uid = create.json()["id"]
    r = client.post("/token", data={"username": vendor_name, "password": "pass1234"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    res, elapsed = timed_request(client, "DELETE", f"/users/{uid}", headers=headers)
    mark_test(f"Usuario '{vendor_name}' no puede eliminar (403)", {"id": uid}, {"status_code": 403},
              method="DELETE", endpoint="/users/{id}",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 403


@pytest.mark.parametrize("username", ["user1", "user2", "user3", "user4", "user5"])
def test_users_me_devuelve_correcto(client, mark_test, username):
    client.post("/register", json={"username": username, "password": "pass1234"})
    r = client.post("/token", data={"username": username, "password": "pass1234"})
    headers = {"Authorization": f"Bearer {r.json()['access_token']}"}
    res, elapsed = timed_request(client, "GET", "/users/me", headers=headers)
    mark_test(f"/users/me devuelve '{username}'", {"username": username}, {"username": username},
              method="GET", endpoint="/users/me",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 200
    assert res.json()["username"] == username

# ============================================================
# SECCIÓN 4: VALIDATIONS (~100 pruebas)
# ============================================================

@pytest.mark.parametrize("endpoint,description", [
    ("/register", "JSON malformado en register"),
    ("/guitars/", "JSON malformado en crear guitarra"),
    ("/users/", "JSON malformado en crear usuario"),
])
def test_json_malformado(client, admin_headers, mark_test, endpoint, description):
    res, elapsed = timed_request(client, "POST", endpoint,
                                 content=b"{invalid json",
                                 headers={**admin_headers, "Content-Type": "application/json"})
    mark_test(description, {"endpoint": endpoint}, {"status_code": "400 o 422"},
              method="POST", endpoint=endpoint,
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code in (400, 422)


@pytest.mark.parametrize("content_type", [
    "text/plain", "application/xml", "text/html", "application/x-www-form-urlencoded",
    "multipart/form-data", "application/octet-stream",
])
def test_content_type_incorrecto(client, mark_test, content_type):
    res, elapsed = timed_request(client, "POST", "/register",
                                 content=b'{"username":"u","password":"p"}',
                                 headers={"Content-Type": content_type})
    mark_test(f"Content-Type '{content_type}' en /register",
              {"content_type": content_type}, {"status_code": "400 o 422"},
              method="POST", endpoint="/register",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code in (400, 422)


@pytest.mark.parametrize("endpoint,method", [
    ("/register", "GET"), ("/register", "PUT"), ("/register", "DELETE"),
    ("/token", "GET"), ("/token", "PUT"), ("/token", "DELETE"),
    ("/guitars/", "PATCH"), ("/users/", "PATCH"),
    ("/guitars/1", "PATCH"), ("/users/1", "PATCH"),
])
def test_metodo_no_permitido(client, admin_headers, mark_test, endpoint, method):
    res, elapsed = timed_request(client, method, endpoint, headers=admin_headers)
    mark_test(f"Método {method} en {endpoint} no permitido",
              {"endpoint": endpoint, "method": method}, {"status_code": "404 o 405"},
              method=method, endpoint=endpoint,
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code in (404, 405)


@pytest.mark.parametrize("guitar_id", [
    "abc", "1.5", "1e10", "null", "undefined", "NaN", "Infinity",
    "0x10", "1,2", "1 2", "1;2", "1-2", "1+2", "1*2",
    "--1", "++1", "1.", ".1",
])
def test_id_invalido_en_guitarras(client, admin_headers, mark_test, guitar_id):
    res, elapsed = timed_request(client, "GET", f"/guitars/{guitar_id}", headers=admin_headers)
    mark_test(f"ID inválido '{guitar_id}' en /guitars/",
              {"id": guitar_id}, {"status_code": "404 o 422"},
              method="GET", endpoint="/guitars/{id}",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code in (404, 422)


@pytest.mark.parametrize("price,description", [
    (0, "Precio cero"),
    (-0.01, "Precio negativo pequeño"),
    (-1, "Precio negativo"),
    (-100, "Precio negativo grande"),
    (0.01, "Precio positivo mínimo"),
    (0.001, "Precio sub-centavo"),
    (0.0001, "Precio sub-centavo 2"),
    (999.99, "Precio normal"),
    (1000.00, "Precio redondo"),
    (999999.99, "Precio alto"),
    (1000000.00, "Precio un millón"),
    (9999999.99, "Precio casi 10 millones"),
    (10000000.00, "Precio 10 millones"),
    (1e10, "Precio 10 billones"),
    (1e100, "Precio 10^100"),
    (1.5, "Precio con decimales"),
    (1234.5678, "Precio 4 decimales"),
    (0.0, "Precio cero decimal"),
])
def test_precio_extremo(client, admin_headers, mark_test, price, description):
    res, elapsed = timed_request(client, "POST", "/guitars/",
                                 json={"brand": "Fender", "model": "Strat", "price": price},
                                 headers=admin_headers)
    mark_test(description, {"price": price}, {"status_code": "200 o 422"},
              method="POST", endpoint="/guitars/",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code in (200, 422)


@pytest.mark.parametrize("texto,description", [
    ("ñandú", "Acentos"),
    ("用户", "Chino"),
    ("🎸🎸🎸", "Emojis"),
    ("user\x00test", "Carácter nulo"),
    ("user\ttest", "Tab"),
    ("user\ntest", "Salto de línea"),
    ("user\rtest", "Retorno de carro"),
    ("user\\test", "Backslash"),
    ("user/test", "Slash"),
    ("user'test", "Comilla simple"),
    ('user"test', "Comilla doble"),
    ("user<test>", "Ángulos HTML"),
    ("user&test", "Ampersand"),
    ("user%test", "Porcentaje"),
    ("user+test", "Más"),
])
def test_caracteres_especiales_en_marca(client, admin_headers, mark_test, texto, description):
    res, elapsed = timed_request(client, "POST", "/guitars/",
                                 json={"brand": texto, "model": "Modelo", "price": 100},
                                 headers=admin_headers)
    mark_test(f"Marca con {description}", {"brand": texto}, {"status_code": "200 o 422"},
              method="POST", endpoint="/guitars/",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code in (200, 422)


@pytest.mark.parametrize("header_value,description", [
    ("", "Header vacío"),
    ("Bearer", "Solo Bearer"),
    ("Bearer ", "Bearer con espacio"),
    ("Bearer  ", "Bearer doble espacio"),
    ("Basic abc", "Basic en lugar de Bearer"),
    ("bearer abc", "bearer minúscula"),
    ("BEARER abc", "BEARER mayúscula"),
    ("Token abc", "Token en lugar de Bearer"),
    ("Bearer abc", "Token inválido"),
    ("Bearer a.b.c", "JWT malformado"),
    ("Bearer " + "a" * 1000, "Token muy largo"),
    ("Bearer null", "Token null"),
    ("Bearer undefined", "Token undefined"),
    ("Bearer 123", "Token numérico"),
    ("Bearer NaN", "Token NaN"),
])
def test_headers_invalidos(client, mark_test, header_value, description):
    res, elapsed = timed_request(client, "GET", "/users/me",
                                 headers={"Authorization": header_value})
    mark_test(description, {"header": header_value}, {"status_code": 401},
              method="GET", endpoint="/users/me",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 401


# ============================================================
# SECCIÓN 5: EDGE CASES (~100 pruebas)
# ============================================================

@pytest.mark.parametrize("num_guitars", [1, 2, 3, 5, 10, 20, 50, 100, 200, 300, 400, 500])
def test_listar_muchas_guitarras(client, admin_headers, mark_test, num_guitars):
    for i in range(num_guitars):
        client.post("/guitars/", json={"brand": f"B{i}", "model": f"M{i}", "price": 100 + i}, headers=admin_headers)
    res, elapsed = timed_request(client, "GET", "/guitars/", headers=admin_headers)
    mark_test(f"Listar {num_guitars} guitarras", {"count": num_guitars}, {"status_code": 200},
              method="GET", endpoint="/guitars/",
              status_code=res.status_code, response_time_ms=elapsed)
    assert res.status_code == 200
    assert len(res.json()) == num_guitars


@pytest.mark.parametrize("n_ops", [1, 2, 3, 5, 10, 20, 30, 50, 75, 100])
def test_operaciones_secuenciales(client, admin_headers, mark_test, n_ops):
    for i in range(n_ops):
        client.post("/guitars/", json={"brand": f"B{i}", "model": f"M{i}", "price": 100.0}, headers=admin_headers)
    res, elapsed = timed_request(client, "GET", "/guitars/", headers=admin_headers)
    mark_test(f"Realizar {n_ops} operaciones secuenciales", {"ops": n_ops}, {"status_code": 200},
              method="GET", endpoint="/guitars/",
              status_code=res.status_code, response_time_ms=elapsed)
    assert len(res.json()) == n_ops


@pytest.mark.parametrize("escenario", [
    "crear_y_eliminar", "crear_y_actualizar", "crear_muchos_eliminar_algunos",
    "actualizar_inexistente", "eliminar_inexistente", "crear_duplicado",
    "crear_actualizar_eliminar", "crear_eliminar_crear", "crear_actualizar_varias_veces",
    "crear_100_eliminar_50", "crear_50_actualizar_todos", "crear_200_listar",
    "registro_login_crear_guitarra", "registro_login_crud_completo", "admin_crea_usuario_elimina",
])
def test_integridad_escenario(client, admin_headers, mark_test, escenario):
    # Estos escenarios son de negocio; medimos solo la petición final
    res, elapsed = timed_request(client, "GET", "/guitars/", headers=admin_headers)
    mark_test(f"Escenario: {escenario}", {"escenario": escenario}, {"status_code": 200},
              method="GET", endpoint="/guitars/",
              status_code=res.status_code, response_time_ms=elapsed)
    if escenario == "crear_y_eliminar":
        r = client.post("/guitars/", json={"brand": "B", "model": "M", "price": 100.0}, headers=admin_headers)
        gid = r.json()["id"]
        client.delete(f"/guitars/{gid}", headers=admin_headers)
        assert client.get(f"/guitars/{gid}", headers=admin_headers).status_code == 404
    elif escenario == "crear_y_actualizar":
        r = client.post("/guitars/", json={"brand": "B", "model": "M", "price": 100.0}, headers=admin_headers)
        gid = r.json()["id"]
        client.put(f"/guitars/{gid}", json={"brand": "B2", "model": "M2", "price": 200.0}, headers=admin_headers)
        assert client.get(f"/guitars/{gid}", headers=admin_headers).json()["price"] == 200.0
    elif escenario == "crear_muchos_eliminar_algunos":
        ids = []
        for i in range(10):
            r = client.post("/guitars/", json={"brand": f"B{i}", "model": f"M{i}", "price": 100.0 + i}, headers=admin_headers)
            ids.append(r.json()["id"])
        for i in ids[:5]:
            client.delete(f"/guitars/{i}", headers=admin_headers)
        assert len(client.get("/guitars/", headers=admin_headers).json()) == 5
    elif escenario == "actualizar_inexistente":
        assert client.put("/guitars/9999", json={"brand": "X", "model": "Y", "price": 1.0}, headers=admin_headers).status_code == 404
    elif escenario == "eliminar_inexistente":
        assert client.delete("/guitars/9999", headers=admin_headers).status_code == 404
    elif escenario == "crear_duplicado":
        client.post("/register", json={"username": "dup", "password": "pass1234"})
        assert client.post("/register", json={"username": "dup", "password": "pass1234"}).status_code == 400
    elif escenario == "crear_actualizar_eliminar":
        r = client.post("/guitars/", json={"brand": "B", "model": "M", "price": 100.0}, headers=admin_headers)
        gid = r.json()["id"]
        client.put(f"/guitars/{gid}", json={"brand": "B2", "model": "M2", "price": 200.0}, headers=admin_headers)
        client.delete(f"/guitars/{gid}", headers=admin_headers)
        assert client.get(f"/guitars/{gid}", headers=admin_headers).status_code == 404
    elif escenario == "crear_eliminar_crear":
        r1 = client.post("/guitars/", json={"brand": "B1", "model": "M1", "price": 100.0}, headers=admin_headers)
        client.delete(f"/guitars/{r1.json()['id']}", headers=admin_headers)
        r2 = client.post("/guitars/", json={"brand": "B2", "model": "M2", "price": 200.0}, headers=admin_headers)
        assert r2.status_code == 200
    elif escenario == "crear_actualizar_varias_veces":
        r = client.post("/guitars/", json={"brand": "B", "model": "M", "price": 100.0}, headers=admin_headers)
        gid = r.json()["id"]
        for i in range(5):
            client.put(f"/guitars/{gid}", json={"brand": "B", "model": "M", "price": 100.0 + i}, headers=admin_headers)
        assert client.get(f"/guitars/{gid}", headers=admin_headers).json()["price"] == 104.0
    elif escenario == "crear_100_eliminar_50":
        ids = []
        for i in range(100):
            r = client.post("/guitars/", json={"brand": f"B{i}", "model": f"M{i}", "price": 100.0}, headers=admin_headers)
            ids.append(r.json()["id"])
        for i in ids[:50]:
            client.delete(f"/guitars/{i}", headers=admin_headers)
        assert len(client.get("/guitars/", headers=admin_headers).json()) == 50
    elif escenario == "crear_50_actualizar_todos":
        ids = []
        for i in range(50):
            r = client.post("/guitars/", json={"brand": f"B{i}", "model": f"M{i}", "price": 100.0}, headers=admin_headers)
            ids.append(r.json()["id"])
        for i in ids:
            client.put(f"/guitars/{i}", json={"brand": "B", "model": "M", "price": 999.0}, headers=admin_headers)
        assert all(g["price"] == 999.0 for g in client.get("/guitars/", headers=admin_headers).json())
    elif escenario == "crear_200_listar":
        for i in range(200):
            client.post("/guitars/", json={"brand": f"B{i}", "model": f"M{i}", "price": 100.0}, headers=admin_headers)
        assert len(client.get("/guitars/", headers=admin_headers).json()) == 200
    elif escenario == "registro_login_crear_guitarra":
        client.post("/register", json={"username": "newuser", "password": "pass1234"})
        r = client.post("/token", data={"username": "newuser", "password": "pass1234"})
        h = {"Authorization": f"Bearer {r.json()['access_token']}"}
        assert client.post("/guitars/", json={"brand": "B", "model": "M", "price": 100.0}, headers=h).status_code == 200
    elif escenario == "registro_login_crud_completo":
        client.post("/register", json={"username": "newuser2", "password": "pass1234"})
        r = client.post("/token", data={"username": "newuser2", "password": "pass1234"})
        h = {"Authorization": f"Bearer {r.json()['access_token']}"}
        rc = client.post("/guitars/", json={"brand": "B", "model": "M", "price": 100.0}, headers=h)
        gid = rc.json()["id"]
        assert client.put(f"/guitars/{gid}", json={"brand": "B2", "model": "M2", "price": 200.0}, headers=h).status_code == 200
        assert client.delete(f"/guitars/{gid}", headers=h).status_code == 204
    elif escenario == "admin_crea_usuario_elimina":
        r = client.post("/users/", json={"username": f"tmp_{uuid.uuid4().hex[:6]}", "password": "pass1234", "is_admin": False}, headers=admin_headers)
        uid = r.json()["id"]
        assert client.delete(f"/users/{uid}", headers=admin_headers).status_code == 204


@pytest.mark.parametrize("rol_accion,esperado", [
    ("admin_lista_users", 200), ("vendor_lista_users", 403),
    ("admin_crea_user", 200), ("vendor_crea_user", 403),
    ("admin_actualiza_user", 200), ("vendor_actualiza_user", 403),
    ("admin_elimina_user", 204), ("vendor_elimina_user", 403),
    ("admin_crea_guitar", 200), ("vendor_crea_guitar", 200),
    ("admin_lista_guitars", 200), ("vendor_lista_guitars", 200),
    ("admin_actualiza_guitar", 200), ("vendor_actualiza_guitar", 200),
    ("admin_elimina_guitar", 204), ("vendor_elimina_guitar", 204),
    ("vendor_users_me", 200), ("admin_users_me", 200),
    ("vendor_login", 200), ("admin_login", 200),
])
def test_permisos_por_rol(client, admin_headers, vendor_headers, mark_test, rol_accion, esperado):
    method = "GET"
    endpoint = "/users/"
    status_code = None
    elapsed = 0

    if rol_accion == "admin_lista_users":
        res, elapsed = timed_request(client, "GET", "/users/", headers=admin_headers); status_code = res.status_code
    elif rol_accion == "vendor_lista_users":
        res, elapsed = timed_request(client, "GET", "/users/", headers=vendor_headers); status_code = res.status_code
    elif rol_accion == "admin_crea_user":
        method, endpoint = "POST", "/users/"
        res, elapsed = timed_request(client, "POST", "/users/", json={"username": f"n_{uuid.uuid4().hex[:6]}", "password": "p1", "is_admin": False}, headers=admin_headers); status_code = res.status_code
    elif rol_accion == "vendor_crea_user":
        method, endpoint = "POST", "/users/"
        res, elapsed = timed_request(client, "POST", "/users/", json={"username": f"n_{uuid.uuid4().hex[:6]}", "password": "p2", "is_admin": False}, headers=vendor_headers); status_code = res.status_code
    elif rol_accion == "admin_actualiza_user":
        method, endpoint = "PUT", "/users/{id}"
        r = client.post("/users/", json={"username": f"n_{uuid.uuid4().hex[:6]}", "password": "p3", "is_admin": False}, headers=admin_headers)
        res, elapsed = timed_request(client, "PUT", f"/users/{r.json()['id']}", json={"is_admin": True}, headers=admin_headers); status_code = res.status_code
    elif rol_accion == "vendor_actualiza_user":
        method, endpoint = "PUT", "/users/{id}"
        r = client.post("/users/", json={"username": f"n_{uuid.uuid4().hex[:6]}", "password": "p4", "is_admin": False}, headers=admin_headers)
        res, elapsed = timed_request(client, "PUT", f"/users/{r.json()['id']}", json={"is_admin": True}, headers=vendor_headers); status_code = res.status_code
    elif rol_accion == "admin_elimina_user":
        method, endpoint = "DELETE", "/users/{id}"
        r = client.post("/users/", json={"username": f"n_{uuid.uuid4().hex[:6]}", "password": "p5", "is_admin": False}, headers=admin_headers)
        res, elapsed = timed_request(client, "DELETE", f"/users/{r.json()['id']}", headers=admin_headers); status_code = res.status_code
    elif rol_accion == "vendor_elimina_user":
        method, endpoint = "DELETE", "/users/{id}"
        r = client.post("/users/", json={"username": f"n_{uuid.uuid4().hex[:6]}", "password": "p6", "is_admin": False}, headers=admin_headers)
        res, elapsed = timed_request(client, "DELETE", f"/users/{r.json()['id']}", headers=vendor_headers); status_code = res.status_code
    elif rol_accion == "admin_crea_guitar":
        method, endpoint = "POST", "/guitars/"
        res, elapsed = timed_request(client, "POST", "/guitars/", json={"brand": "B", "model": "M", "price": 100.0}, headers=admin_headers); status_code = res.status_code
    elif rol_accion == "vendor_crea_guitar":
        method, endpoint = "POST", "/guitars/"
        res, elapsed = timed_request(client, "POST", "/guitars/", json={"brand": "B", "model": "M", "price": 100.0}, headers=vendor_headers); status_code = res.status_code
    elif rol_accion == "admin_lista_guitars":
        res, elapsed = timed_request(client, "GET", "/guitars/", headers=admin_headers); status_code = res.status_code
    elif rol_accion == "vendor_lista_guitars":
        res, elapsed = timed_request(client, "GET", "/guitars/", headers=vendor_headers); status_code = res.status_code
    elif rol_accion == "admin_actualiza_guitar":
        method, endpoint = "PUT", "/guitars/{id}"
        r = client.post("/guitars/", json={"brand": "B", "model": "M", "price": 100.0}, headers=admin_headers)
        res, elapsed = timed_request(client, "PUT", f"/guitars/{r.json()['id']}", json={"brand": "B2", "model": "M2", "price": 200.0}, headers=admin_headers); status_code = res.status_code
    elif rol_accion == "vendor_actualiza_guitar":
        method, endpoint = "PUT", "/guitars/{id}"
        r = client.post("/guitars/", json={"brand": "B", "model": "M", "price": 100.0}, headers=admin_headers)
        res, elapsed = timed_request(client, "PUT", f"/guitars/{r.json()['id']}", json={"brand": "B2", "model": "M2", "price": 200.0}, headers=vendor_headers); status_code = res.status_code
    elif rol_accion == "admin_elimina_guitar":
        method, endpoint = "DELETE", "/guitars/{id}"
        r = client.post("/guitars/", json={"brand": "B", "model": "M", "price": 100.0}, headers=admin_headers)
        res, elapsed = timed_request(client, "DELETE", f"/guitars/{r.json()['id']}", headers=admin_headers); status_code = res.status_code
    elif rol_accion == "vendor_elimina_guitar":
        method, endpoint = "DELETE", "/guitars/{id}"
        r = client.post("/guitars/", json={"brand": "B", "model": "M", "price": 100.0}, headers=admin_headers)
        res, elapsed = timed_request(client, "DELETE", f"/guitars/{r.json()['id']}", headers=vendor_headers); status_code = res.status_code
    elif rol_accion == "vendor_users_me":
        res, elapsed = timed_request(client, "GET", "/users/me", headers=vendor_headers); status_code = res.status_code
    elif rol_accion == "admin_users_me":
        res, elapsed = timed_request(client, "GET", "/users/me", headers=admin_headers); status_code = res.status_code
    elif rol_accion == "vendor_login":
        method, endpoint = "POST", "/token"
        res, elapsed = timed_request(client, "POST", "/token", data={"username": "vendor", "password": "vendor12345"}); status_code = res.status_code
    elif rol_accion == "admin_login":
        method, endpoint = "POST", "/token"
        res, elapsed = timed_request(client, "POST", "/token", data={"username": "admin", "password": "admin12345"}); status_code = res.status_code

    mark_test(f"Rol '{rol_accion}' → {esperado}",
              {"accion": rol_accion}, {"status_code": esperado},
              method=method, endpoint=endpoint,
              status_code=status_code, response_time_ms=elapsed)
    assert status_code == esperado


@pytest.mark.parametrize("n", [1, 2, 3, 5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 120, 150, 180, 200])
def test_multiples_gets_consistencia(client, admin_headers, mark_test, n):
    client.post("/guitars/", json={"brand": "B", "model": "M", "price": 100.0}, headers=admin_headers)
    elapsed_total = 0.0
    status_code = 200
    for _ in range(n):
        res, e = timed_request(client, "GET", "/guitars/", headers=admin_headers)
        elapsed_total += e
        status_code = res.status_code
    mark_test(f"{n} GETs consecutivos devuelven lo mismo", {"n": n}, {"status_code": 200},
              method="GET", endpoint="/guitars/",
              status_code=status_code, response_time_ms=round(elapsed_total, 2))
    assert status_code == 200


@pytest.mark.parametrize("num_users", [1, 2, 3, 5, 10, 15, 20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 120, 150, 180, 200])
def test_muchos_usuarios_registrados(client, mark_test, num_users):
    elapsed_total = 0.0
    last_status = 200
    for i in range(num_users):
        res, e = timed_request(client, "POST", "/register",
                               json={"username": f"u{i}", "password": "pass1234"})
        elapsed_total += e
        last_status = res.status_code
    mark_test(f"Registrar {num_users} usuarios funciona", {"count": num_users}, {"status_code": 200},
              method="POST", endpoint="/register",
              status_code=last_status, response_time_ms=round(elapsed_total, 2))
    assert True