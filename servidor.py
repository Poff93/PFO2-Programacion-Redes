import os
import sqlite3
import threading
from contextlib import contextmanager

from flask import Flask, jsonify, render_template_string, request, session
from werkzeug.security import check_password_hash, generate_password_hash


app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "clave_pfo2_ifts29_secret_key_prod")
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
DB_NAME = "pfo2_gestion.db"
db_lock = threading.Lock()


@contextmanager
def obtener_conexion():
    conn = sqlite3.connect(DB_NAME, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


def inicializar_db():
    try:
        with db_lock:
            with obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS usuarios (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        usuario TEXT UNIQUE NOT NULL,
                        password_hash TEXT NOT NULL,
                        fecha_registro TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS tareas (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        usuario_id INTEGER NOT NULL,
                        titulo TEXT NOT NULL,
                        estado TEXT DEFAULT 'pendiente',
                        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
                            ON DELETE CASCADE
                    )
                    """
                )
                conn.commit()

        print("Base de datos SQLite inicializada correctamente.")
    except sqlite3.Error as error:
        print(f"Error al inicializar la base de datos: {error}")


@app.route("/registro", methods=["POST"])
def registro():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify({"error": "Se requiere un objeto JSON válido."}), 400

    usuario = datos.get("usuario")
    password = datos.get("contraseña") or datos.get("password") or datos.get("contrasena")

    if not isinstance(usuario, str) or not isinstance(password, str):
        return jsonify({"error": "El usuario y la contraseña deben ser textos."}), 400

    usuario = usuario.strip()
    password = password.strip()

    if not usuario or not password:
        return jsonify({"error": "Debe completar usuario y contraseña."}), 400
    if len(usuario) < 3:
        return jsonify({"error": "El nombre de usuario debe tener al menos 3 caracteres."}), 400
    if len(password) < 8:
        return jsonify({"error": "La contraseña debe tener al menos 8 caracteres."}), 400

    password_hash = generate_password_hash(password)

    try:
        with db_lock:
            with obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO usuarios (usuario, password_hash) VALUES (?, ?)",
                    (usuario, password_hash),
                )
                conn.commit()
                usuario_id = cursor.lastrowid

        return jsonify(
            {
                "mensaje": f"Usuario '{usuario}' registrado correctamente.",
                "usuario_id": usuario_id,
            }
        ), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": f"El usuario '{usuario}' ya se encuentra registrado."}), 409
    except sqlite3.Error as error:
        return jsonify({"error": f"Error de base de datos: {error}"}), 500


@app.route("/login", methods=["POST"])
def login():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify({"error": "Se requiere un objeto JSON válido."}), 400

    usuario = datos.get("usuario")
    password = datos.get("contraseña") or datos.get("password") or datos.get("contrasena")

    if not isinstance(usuario, str) or not isinstance(password, str):
        return jsonify({"error": "Ingrese textos válidos para usuario y contraseña."}), 400

    usuario = usuario.strip()
    password = password.strip()

    if not usuario or not password:
        return jsonify({"error": "Ingrese usuario y contraseña."}), 400

    try:
        with db_lock:
            with obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, usuario, password_hash FROM usuarios WHERE usuario = ?",
                    (usuario,),
                )
                fila = cursor.fetchone()

        if not fila or not check_password_hash(fila["password_hash"], password):
            return jsonify({"error": "Credenciales inválidas."}), 401

        session["usuario_id"] = fila["id"]
        session["usuario"] = fila["usuario"]

        return jsonify(
            {
                "mensaje": f"Bienvenido/a {fila['usuario']}.",
                "usuario_id": fila["id"],
                "usuario": fila["usuario"],
            }
        ), 200
    except sqlite3.Error as error:
        return jsonify({"error": f"Error de base de datos: {error}"}), 500


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"mensaje": "Sesión cerrada correctamente."}), 200


HTML_BIENVENIDA = """
<div>
  <h1>Sistema de Gestión de Tareas - PFO 2</h1>
  <p>
    API REST desarrollada con Flask y SQLite para Programación sobre Redes
    (IFTS Nº 29).
  </p>
  <p>Endpoints disponibles:</p>
  <ul>
    <li>POST /registro</li>
    <li>POST /login</li>
    <li>POST /logout</li>
    <li>GET /tareas</li>
    <li>POST /tareas</li>
  </ul>
</div>
"""


@app.route("/tareas", methods=["GET"])
def listar_tareas():
    wants_json = (
        request.headers.get("Accept") == "application/json"
        or request.args.get("format") == "json"
    )

    if not wants_json and "usuario_id" not in session:
        return render_template_string(HTML_BIENVENIDA), 200

    if "usuario_id" not in session:
        return jsonify({"error": "No autorizado. Debe iniciar sesión primero."}), 401

    usuario_id = session["usuario_id"]

    try:
        with db_lock:
            with obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, titulo, estado, fecha_creacion
                    FROM tareas
                    WHERE usuario_id = ?
                    ORDER BY fecha_creacion DESC
                    """,
                    (usuario_id,),
                )
                filas = cursor.fetchall()

        tareas = [dict(fila) for fila in filas]
        return jsonify(
            {
                "usuario": session["usuario"],
                "total": len(tareas),
                "tareas": tareas,
            }
        ), 200
    except sqlite3.Error as error:
        return jsonify({"error": f"Error de base de datos: {error}"}), 500


@app.route("/tareas", methods=["POST"])
def crear_tarea():
    if "usuario_id" not in session:
        return jsonify({"error": "No autorizado. Debe iniciar sesión primero."}), 401

    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify({"error": "Se requiere un objeto JSON válido."}), 400

    titulo = datos.get("titulo")
    if not isinstance(titulo, str) or not titulo.strip():
        return jsonify({"error": "El título de la tarea no puede estar vacío."}), 400

    titulo = titulo.strip()
    if len(titulo) > 150:
        return jsonify({"error": "El título supera el máximo de 150 caracteres."}), 400

    try:
        with db_lock:
            with obtener_conexion() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO tareas (usuario_id, titulo) VALUES (?, ?)",
                    (session["usuario_id"], titulo),
                )
                conn.commit()
                tarea_id = cursor.lastrowid

        return jsonify(
            {
                "mensaje": "Tarea creada correctamente.",
                "tarea_id": tarea_id,
                "titulo": titulo,
            }
        ), 201
    except sqlite3.IntegrityError:
        return jsonify({"error": "El usuario de la sesión no existe."}), 400
    except sqlite3.Error as error:
        return jsonify({"error": f"Error de base de datos: {error}"}), 500


if __name__ == "__main__":
    inicializar_db()
    app.run(host="localhost", port=5000, debug=False)
