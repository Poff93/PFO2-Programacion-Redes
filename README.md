# Práctica Formativa Obligatoria 2 (PFO 2) - API REST y autenticación

**Materia:** Programación sobre Redes (IFTS Nº 29)  
**Carrera:** Tecnicatura Superior en Desarrollo de Software  
**Alumno:** Pablo Off  
**Comisión:** D
**Docente:** Germán Ríos
**Repositorio GitHub:** https://github.com/Poff93/PFO2-Programacion-Redes

## Descripción del proyecto

Aplicación cliente-servidor desarrollada con Flask y SQLite. El proyecto implementa una API REST con sesiones HTTP, validación de datos, almacenamiento seguro de contraseñas y un cliente interactivo de consola.

El usuario autenticado se obtiene de la sesión del servidor. Por eso, las operaciones sobre tareas no aceptan un `usuario_id` enviado por el cliente.

## Funcionalidades

- Registro de usuarios con validación de datos.
- Contraseñas almacenadas mediante hashes generados por Werkzeug.
- Inicio y cierre de sesión usando cookies de sesión firmadas por Flask.
- Consulta de tareas pertenecientes al usuario autenticado.
- Creación de tareas con títulos de hasta 150 caracteres.
- Integridad referencial entre usuarios y tareas mediante SQLite.
- Cliente de consola con contraseña oculta y manejo de errores de conexión.

## Endpoints de la API

### `POST /registro`

Registra un usuario nuevo. El nombre debe tener al menos 3 caracteres y la contraseña, al menos 8.

```json
{
  "usuario": "Pablo",
  "contraseña": "12345678"
}
```

Respuesta exitosa: `201 Created`.

### `POST /login`

Valida las credenciales y crea una sesión HTTP para el usuario.

Respuesta exitosa: `200 OK`.

### `POST /logout`

Elimina la sesión activa.

Respuesta exitosa: `200 OK`.

### `GET /tareas`

- Sin sesión y mediante un navegador: muestra la página HTML de bienvenida.
- Sin sesión y solicitando JSON: responde `401 Unauthorized`.
- Con sesión activa: devuelve las tareas del usuario autenticado en formato JSON.

### `POST /tareas`

Crea una tarea asociada al usuario guardado en la sesión actual.

```json
{
  "titulo": "Estudiar para la entrega"
}
```

Respuesta exitosa: `201 Created`.

## Requisitos

- Python 3.10 o superior.
- Flask.
- Requests.

## Instalación

Desde la terminal, ejecutar:

```bash
python -m pip install -r requirements.txt
```

En Windows PowerShell se puede definir una clave de sesión propia para el entorno actual:

```powershell
$env:SECRET_KEY = "reemplazar-por-una-clave-segura"
```

## Ejecución

### 1. Iniciar el servidor

```bash
python servidor.py
```

La API estará disponible en `http://localhost:5000`.

### 2. Iniciar el cliente

En otra terminal:

```bash
python cliente.py
```

La base de datos `pfo2_gestion.db` se crea automáticamente al iniciar el servidor.

## Verificación rápida

Para comprobar la sintaxis de los archivos Python:

```bash
python -m py_compile servidor.py cliente.py
```

El flujo esperado es:

1. Registrar un usuario.
2. Iniciar sesión.
3. Crear una tarea.
4. Consultar las tareas.
5. Cerrar sesión.

## Seguridad y decisiones técnicas

- Las consultas SQL utilizan parámetros para evitar inyección SQL.
- SQLite tiene activadas las claves foráneas.
- Las contraseñas nunca se guardan en texto plano.
- La cookie de sesión utiliza las opciones `HttpOnly` y `SameSite=Lax`.
- El servidor se ejecuta con `debug=False`.
- Las tareas se asocian al usuario de la sesión y no a un ID recibido desde el cliente.

## Estructura del proyecto

- `servidor.py`: API Flask, autenticación, sesiones y acceso a SQLite.
- `cliente.py`: cliente interactivo por consola.
- `pfo2_gestion.db`: base de datos SQLite generada automáticamente.
- `README.md`: documentación del proyecto.

## Limitaciones actuales

- El proyecto está pensado para ejecutarse localmente.
- No incluye todavía modificación ni eliminación de tareas.
- Para producción sería necesario utilizar HTTPS y una clave secreta administrada mediante variables de entorno.

## Respuestas conceptuales

### ¿Por qué hashear las contraseñas?

Las contraseñas no deben guardarse en texto plano. El servidor almacena un hash generado con Werkzeug y, al iniciar sesión, verifica la contraseña ingresada contra ese hash. Si alguien accede a la base de datos, no obtiene directamente las contraseñas originales. El uso de hashes con sal única también dificulta los ataques con tablas precalculadas. El hash no debe confundirse con cifrado: no está pensado para recuperar la contraseña original.

### ¿Qué ventajas tiene SQLite en este proyecto?

SQLite no requiere instalar ni administrar un servidor de base de datos aparte: los datos se guardan en un archivo local y las consultas se realizan desde Python. Es sencillo de configurar y suficiente para una aplicación pequeña ejecutada localmente. Para sistemas con mucha concurrencia o varios servidores, convendría evaluar una base de datos cliente-servidor.
