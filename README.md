# Sistema de Biblioteca - API REST

Esta es una API REST completa para un **Sistema de Biblioteca** construida con **Python, Flask, SQLite y Flask-SQLAlchemy**. La aplicación sigue una arquitectura limpia en capas para facilitar el mantenimiento y la escalabilidad, y cuenta con un sistema robusto de autenticación y autorización basado en roles (Admin/Lector) con JWT.

## Características Principales y Reglas de Negocio
- **Autenticación con JWT**: Rutas protegidas que diferencian accesos para Administradores y Lectores.
- **Gestión de Stock y Cola de Reserva FIFO**:
  - Un libro solo puede prestarse si `cantidad_disponible > 0`.
  - Si no hay stock general disponible, un usuario puede crear una reserva. Esta entra en una cola ordenada de manera FIFO por libro.
  - Al devolver un libro, si hay reservas pendientes para dicho libro, el primer usuario en la cola es notificado automáticamente (se marca su reserva como `notificada` y se le otorga un plazo de 48 horas para retirarlo).
  - Durante las 48 horas de vigencia de la notificación, el stock disponible de esa copia queda bloqueado con prioridad y solo puede ser prestado al usuario que posee la reserva notificada.
- **Cálculo de Multas Automatizado**: Al devolver un libro tarde (después de la fecha estimada de devolución), el sistema genera automáticamente una multa calculada como `días de atraso * TARIFA_DIARIA` ($2.0 por día).
- **Restricciones del Lector**:
  - Un lector no puede tener más de 3 préstamos activos simultáneos.
  - Un lector con multas pendientes (estado `pendiente`) no puede solicitar nuevos préstamos ni reservas hasta saldarlas.
- **Gestión y Reportes de Admin**: Los administradores pueden dar de alta/baja libros (baja lógica), modificar usuarios (activar/suspender), pagar o consultar multas, y obtener reportes avanzados de rendimiento de la biblioteca.

---

## Estructura del Proyecto

El código está organizado en las siguientes capas y carpetas:
- **`app.py`**: Punto de entrada de la aplicación, configuración de extensiones (SQLAlchemy, JWT) y manejadores globales de errores.
- **`config.py`**: Parámetros de configuración del sistema (claves secretas, URI de base de datos) y constantes de negocio.
- **`models/`**: Definición de los modelos de base de datos SQLAlchemy:
  - `Libro`, `Usuario`, `Prestamo`, `Reserva`, `Multa`.
- **`schemas/`**: Esquemas de Marshmallow para la validación de entrada y serialización de salida JSON.
- **`services/`**: Lógica centralizada de negocio (préstamos, devoluciones, control de la cola FIFO y expiración de reservas).
- **`routes/`**: Controladores de la API (Blueprints) expuestos por recursos.
- **`utils/`**: Decoradores personalizados para seguridad (`@admin_required`, `@active_user_required`).
- **`seed.py`**: Script para poblar la base de datos con registros iniciales de prueba.
- **`tests.py`**: Pruebas unitarias e integración que validan todo el sistema.

---

## Instalación y Configuración

Sigue estos pasos para ejecutar la API localmente en tu sistema Windows:

### 1. Clonar o acceder al directorio del proyecto
Asegúrate de estar en el directorio raíz de la aplicación:
```bash
cd "d:\Proyectos\API rest"
```

### 2. Crear e iniciar el entorno virtual
```powershell
python -m venv venv
venv\Scripts\activate
```

### 3. Instalar las dependencias
```bash
pip install -r requirements.txt
```

### 4. Población inicial de la base de datos (Seed)
Este script creará las tablas en SQLite y cargará registros de prueba (usuarios, libros, préstamos vencidos y stock agotado):
```bash
python seed.py
```


### 5. Iniciar el Servidor de Desarrollo
```bash
python app.py
```
El servidor se iniciará en `http://127.0.0.1:5000`.

---

## Cuentas de Prueba creadas por `seed.py`
Para facilitar el uso y las pruebas de la API, el script `seed.py` crea las siguientes credenciales:

| Nombre | Correo Electrónico | Rol | Contraseña | Estado Inicial |
| :--- | :--- | :--- | :--- | :--- |
| Administrador General | `admin@biblioteca.com` | `admin` | `admin123` | Activo |
| Juan Pérez | `juan@correo.com` | `lector` | `lector123` | Activo (Tiene en préstamo activo "1984") |
| María Gómez | `maria@correo.com` | `lector` | `lector123` | Activo (Tiene un préstamo vencido de "Don Quijote") |
| Usuario Suspendido | `suspendido@correo.com` | `lector` | `lector123` | Suspendido |

---

## Endpoints de la API

### 1. Autenticación
- **`POST /auth/register`**: Registra un nuevo usuario.
- **`POST /auth/login`**: Inicia sesión y devuelve un token JWT.

### 2. Libros
- **`GET /libros`**: Catálogo completo (soporta filtros query: `categoria`, `autor`, `disponibilidad=true/false`, `search`).
- **`GET /libros/<id>`**: Obtiene el detalle de un libro específico.
- **`POST /libros`**: Agrega un nuevo libro (Solo Admin).
- **`PUT /libros/<id>`**: Actualiza la información de un libro (Solo Admin).
- **`DELETE /libros/<id>`**: Realiza una baja lógica del libro (Solo Admin).
- **`GET /libros/<id>/cola-reservas`**: Consulta la cola de reservas pendientes de un libro (Solo Admin).

### 3. Usuarios (Solo Admin)
- **`GET /usuarios`**: Lista todos los usuarios.
- **`GET /usuarios/<id>`**: Detalle de un usuario.
- **`PUT /usuarios/<id>`**: Actualiza datos de un usuario, como su rol o suspenderlo/activarlo (`estado: "suspendido"` / `estado: "activo"`).
- **`DELETE /usuarios/<id>`**: Elimina físicamente un usuario (siempre que no tenga préstamos activos).

### 4. Préstamos
- **`GET /prestamos`**: Lista los préstamos (Admin ve todos, Lectores solo los propios).
- **`GET /prestamos/<id>`**: Detalle de un préstamo.
- **`POST /prestamos`**: Crea un préstamo. Un Lector solo puede crearlo para sí mismo (se infiere del token). El Admin debe pasar `"id_usuario"`.
- **`PUT /prestamos/<id>/devolver`**: Marca la devolución de un libro, calcula multas si hay retraso y notifica al siguiente usuario en cola de reservas.

### 5. Reservas
- **`GET /reservas`**: Lista las reservas (Admin ve todas, Lectores solo las propias).
- **`POST /reservas`**: Reserva un libro sin stock general.
- **`PUT /reservas/<id>/cancelar`**: Cancela una reserva y reorganiza las posiciones FIFO de los siguientes usuarios.

### 6. Multas
- **`GET /multas`**: Lista las multas generadas (Admin ve todas, Lectores solo las propias).
- **`PUT /multas/<id>/pagar`**: Salda una multa pendiente.

### 7. Reportes (Solo Admin)
- **`GET /reportes/libros-mas-prestados`**: Lista del Top de libros con más préstamos registrados.
- **`GET /reportes/usuarios-con-multas`**: Lista de usuarios con deudas activas y el total adeudado.
- **`GET /reportes/prestamos-vencidos`**: Lista de préstamos en curso cuya fecha de entrega esperada ya venció.

---

## Ejemplos de uso con `curl`

### A. Registro e Inicio de Sesión de Lector
Para registrar e iniciar sesión como un nuevo lector:

```bash
# 1. Registrar
curl -X POST http://127.0.0.1:5000/auth/register \
  -H "Content-Type: application/json" \
  -d "{\"nombre\": \"Carlos Gomez\", \"email\": \"carlos@correo.com\", \"password\": \"carlos123\"}"

# 2. Login
curl -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"carlos@correo.com\", \"password\": \"carlos123\"}"
```
*Guarda el token devuelto en la respuesta para usarlo en los siguientes comandos.*

### B. Préstamo de Libro Disponible
```bash
curl -X POST http://127.0.0.1:5000/prestamos \
  -H "Authorization: Bearer <TU_TOKEN_JWT>" \
  -H "Content-Type: application/json" \
  -d "{\"id_libro\": 1}"
```

### C. Reservar un Libro sin Stock (Cola FIFO)
El libro con ID `2` ("1984") se encuentra agotado inicialmente tras ejecutar `seed.py`. Intenta reservarlo:
```bash
curl -X POST http://127.0.0.1:5000/reservas \
  -H "Authorization: Bearer <TU_TOKEN_JWT>" \
  -H "Content-Type: application/json" \
  -d "{\"id_libro\": 2}"
```
*Recibirás una respuesta indicando que tu posición en la cola es la número 1.*

### D. Devolución de Libro y Generación de Multa
Para probar la generación de multas, podemos loguearnos con la cuenta de María Gómez (`maria@correo.com` / `lector123`), quien tiene un préstamo atrasado de "Don Quijote" (ID de préstamo: `2`).

```bash
# 1. Login de Maria para obtener su token
curl -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"maria@correo.com\", \"password\": \"lector123\"}"

# 2. Realizar la devolución
curl -X PUT http://127.0.0.1:5000/prestamos/2/devolver \
  -H "Authorization: Bearer <TOKEN_DE_MARIA>"
```
*La API devolverá un JSON indicando éxito y mostrando la multa generada junto con los días de retraso.*

### E. Pago de Multa
Si María intenta pedir otro préstamo, la API le denegará el acceso debido a su multa pendiente. Debe saldarla:
```bash
curl -X PUT http://127.0.0.1:5000/multas/1/pagar \
  -H "Authorization: Bearer <TOKEN_DE_MARIA>"
```

### F. Consultar Reporte de Administrador
```bash
# 1. Login de Admin
curl -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"admin@biblioteca.com\", \"password\": \"admin123\"}"

# 2. Consultar libros más prestados
curl -X GET http://127.0.0.1:5000/reportes/libros-mas-prestados \
  -H "Authorization: Bearer <TOKEN_DEL_ADMIN>"
```
