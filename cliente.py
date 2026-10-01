import getpass

import requests


URL_BASE = "http://localhost:5000"
MIN_PASSWORD_LENGTH = 8
MAX_TITLE_LENGTH = 150


def registrarse(session):
    print("\n--- REGISTRO DE USUARIO ---")
    usuario = input("Nombre de usuario: ").strip()
    password = getpass.getpass("Contraseña (mínimo 8 caracteres): ").strip()

    if not usuario or not password:
        print("El usuario y la contraseña no pueden estar vacíos.")
        return
    if len(usuario) < 3:
        print("El usuario debe tener al menos 3 caracteres.")
        return
    if len(password) < MIN_PASSWORD_LENGTH:
        print("La contraseña debe tener al menos 8 caracteres.")
        return

    try:
        respuesta = session.post(
            f"{URL_BASE}/registro",
            json={"usuario": usuario, "contraseña": password},
            timeout=5,
        )
        datos = respuesta.json()

        if respuesta.status_code == 201:
            print(f"> {datos.get('mensaje')}")
        else:
            print(f"> Error ({respuesta.status_code}): {datos.get('error')}")
    except requests.exceptions.RequestException as error:
        print(f"> Error de conexión con la API: {error}")
    except ValueError:
        print("> La API devolvió una respuesta no válida.")


def iniciar_sesion(session):
    print("\n--- INICIO DE SESIÓN ---")
    usuario = input("Nombre de usuario: ").strip()
    password = getpass.getpass("Contraseña: ").strip()

    if not usuario or not password:
        print("El usuario y la contraseña no pueden estar vacíos.")
        return None

    try:
        respuesta = session.post(
            f"{URL_BASE}/login",
            json={"usuario": usuario, "contraseña": password},
            timeout=5,
        )
        datos = respuesta.json()

        if respuesta.status_code == 200:
            print(f"> {datos.get('mensaje')}")
            return {"id": datos.get("usuario_id"), "usuario": datos.get("usuario")}

        print(f"> Error ({respuesta.status_code}): {datos.get('error')}")
        return None
    except requests.exceptions.RequestException as error:
        print(f"> Error de conexión con la API: {error}")
        return None
    except ValueError:
        print("> La API devolvió una respuesta no válida.")
        return None


def cerrar_sesion(session):
    try:
        respuesta = session.post(f"{URL_BASE}/logout", timeout=5)
        datos = respuesta.json()
        print(f"> {datos.get('mensaje')}")
    except requests.exceptions.RequestException as error:
        print(f"> Error al cerrar sesión: {error}")
    except ValueError:
        print("> La API devolvió una respuesta no válida.")


def ver_tareas(session):
    print("\n--- MIS TAREAS ---")

    try:
        respuesta = session.get(
            f"{URL_BASE}/tareas",
            headers={"Accept": "application/json"},
            timeout=5,
        )
        datos = respuesta.json()

        if respuesta.status_code == 200:
            tareas = datos.get("tareas", [])
            print(f"Usuario: {datos.get('usuario')} | Total: {datos.get('total')}")

            if tareas:
                print("-" * 40)
                for tarea in tareas:
                    print(
                        f"[{tarea['id']}] {tarea['titulo']} "
                        f"({tarea['estado']}) - {tarea['fecha_creacion']}"
                    )
                print("-" * 40)
            else:
                print("No tenés tareas registradas todavía.")
        else:
            print(f"> Error ({respuesta.status_code}): {datos.get('error')}")
    except requests.exceptions.RequestException as error:
        print(f"> Error de conexión con la API: {error}")
    except ValueError:
        print("> La API devolvió una respuesta no válida.")


def crear_tarea(session):
    print("\n--- NUEVA TAREA ---")
    titulo = input("Título de la tarea (máximo 150 caracteres): ").strip()

    if not titulo:
        print("El título no puede estar vacío.")
        return
    if len(titulo) > MAX_TITLE_LENGTH:
        print("El título no puede superar los 150 caracteres.")
        return

    try:
        respuesta = session.post(
            f"{URL_BASE}/tareas",
            json={"titulo": titulo},
            timeout=5,
        )
        datos = respuesta.json()

        if respuesta.status_code == 201:
            print(f"> {datos.get('mensaje')} (ID: {datos.get('tarea_id')})")
        else:
            print(f"> Error ({respuesta.status_code}): {datos.get('error')}")
    except requests.exceptions.RequestException as error:
        print(f"> Error de conexión con la API: {error}")
    except ValueError:
        print("> La API devolvió una respuesta no válida.")


def main():
    session = requests.Session()
    usuario_logueado = None

    print("=" * 42)
    print("   Sistema de Gestión de Tareas - PFO 2")
    print("=" * 42)

    while True:
        estado = usuario_logueado["usuario"] if usuario_logueado else "Sin sesión"
        print(f"\n[ Usuario actual: {estado} ]")
        print("1. Registrarse")
        print("2. Iniciar sesión")
        print("3. Ver mis tareas")
        print("4. Crear nueva tarea")
        print("5. Cerrar sesión")
        print("6. Salir")

        try:
            opcion = input("\nElegí una opción (1-6): ").strip()
        except KeyboardInterrupt:
            print("\nSaliendo...")
            break

        if opcion == "1":
            registrarse(session)
        elif opcion == "2":
            usuario = iniciar_sesion(session)
            if usuario:
                usuario_logueado = usuario
        elif opcion == "3":
            if usuario_logueado:
                ver_tareas(session)
            else:
                print("Debés iniciar sesión primero.")
        elif opcion == "4":
            if usuario_logueado:
                crear_tarea(session)
            else:
                print("Debés iniciar sesión primero.")
        elif opcion == "5":
            if usuario_logueado:
                cerrar_sesion(session)
                usuario_logueado = None
            else:
                print("No hay ninguna sesión activa.")
        elif opcion == "6":
            if usuario_logueado:
                cerrar_sesion(session)
            print("Hasta luego.")
            break
        else:
            print("Opción no válida. Intentá de nuevo.")


if __name__ == "__main__":
    main()
