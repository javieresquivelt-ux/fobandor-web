# Guía Paso a Paso: Configuración de Google Cloud Console para Login con Gmail

> **Proyecto:** FOBANDOR (`www.fobandor.com`)  
> **Propósito:** Configurar credenciales OAuth 2.0 para que cualquier cliente pueda registrarse e iniciar sesión con un solo clic usando su cuenta personal de Gmail (`@gmail.com`).  
> **Costo:** 100% Gratuito (Google no cobra por autenticación OAuth ni requiere tarjeta de crédito).  
> **Tiempo estimado:** 5 a 10 minutos.

---

## Prerrequisitos

* Una cuenta de Google/Gmail personal o corporativa común y corriente (ej. `tu-correo@gmail.com`).
* Navegador web abierto.
* Proyecto FOBANDOR clonado en tu máquina local.

---

## Paso 1: Acceder a Google Cloud y Crear un Proyecto

1. Ingresa a la consola de desarrolladores de Google Cloud:  
   👉 **[https://console.cloud.google.com/](https://console.cloud.google.com/)**
2. Inicia sesión con tu cuenta de Gmail.
3. Si es tu primera vez en la consola, acepta los Términos y Condiciones generales (marca tu país y presiona **"Aceptar y continuar"**).
4. En la barra superior azul, haz clic en el selector desplegable de proyectos (junto al texto *"Google Cloud"* o donde dice *"Seleccionar un proyecto"*).
5. En la ventana emergente, haz clic en el botón superior derecho: **"PROYECTO NUEVO"** (o *"New Project"*).
6. Completa el formulario:
   * **Nombre del proyecto:** `fobandor-web` (o `FOBANDOR`).
   * **Organización:** Déjalo en *"Sin organización"* (no es necesario cambiarlo).
7. Haz clic en **"CREAR"**.
8. Espera unos 10 segundos hasta que la notificación en la esquina superior derecha confirme la creación del proyecto y haz clic en **"SELECCIONAR PROYECTO"** (asegúrate de que en la barra superior aparezca seleccionado `fobandor-web`).

---

## Paso 2: Configurar la Pantalla de Consentimiento OAuth

La pantalla de consentimiento es la interfaz oficial de Google que ve el usuario cuando hace clic en *"Continuar con Google"*, donde se le pregunta: *"FOBANDOR desea acceder a tu nombre y correo electrónico"*.

1. En el menú lateral izquierdo (icono de 3 líneas horizontales `☰`), navega a:  
   👉 **APIs y servicios** > **Pantalla de consentimiento de OAuth**  
   *(o busca "Pantalla de consentimiento de OAuth" en el buscador superior).*
2. **Tipo de usuario (User Type):**
   * Selecciona la opción: **"Externo"** (External).  
     *(Esta opción permite que cualquier persona con una cuenta Gmail pueda iniciar sesión).*
   * Haz clic en **"CREAR"**.
3. **Paso 1 del asistente: "Información de la aplicación":**
   * **Nombre de la aplicación:** `FOBANDOR`
   * **Correo electrónico de asistencia del usuario:** Selecciona tu correo Gmail del desplegable.
   * **Logotipo de la aplicación:** Déjalo vacío por ahora (opcional).
   * **Dominio de la aplicación:**
     * *Página principal de la aplicación:* Déjalo vacío en local (o `https://www.fobandor.com`).
     * *Vínculo a la Política de Privacidad:* Déjalo vacío en local.
     * *Vínculo a las Condiciones del Servicio:* Déjalo vacío en local.
   * **Datos de contacto del desarrollador:**
     * *Direcciones de correo electrónico:* Ingresa nuevamente tu correo Gmail.
   * Haz clic en el botón inferior: **"GUARDAR Y CONTINUAR"**.
4. **Paso 2 del asistente: "Permisos" (Scopes):**
   * Haz clic en el botón **"AGREGAR O QUITAR PERMISOS"**.
   * En el panel lateral que se abre, marca las dos primeras casillas bajo *"Permisos no confidenciales"*:
     * `.../auth/userinfo.email` (Ver tu dirección de correo electrónico principal).
     * `.../auth/userinfo.profile` (Ver tu información de perfil personal pública).
   * Haz clic en **"ACTUALIZAR"** al final del panel lateral.
   * Haz clic en **"GUARDAR Y CONTINUAR"**.
5. **Paso 3 del asistente: "Usuarios de prueba" (Test Users):**
   * *¿Por qué este paso?* Mientras la aplicación está en modo de desarrollo ("En pruebas"), Google exige registrar explícitamente qué correos pueden hacer login.
   * Haz clic en **"+ AGREGAR USUARIOS"**.
   * Escribe tu dirección de correo Gmail personal (y cualquier otra que quieras usar para probar, por ejemplo la de Freddy Obando).
   * Haz clic en **"AGREGAR"**.
   * Haz clic en **"GUARDAR Y CONTINUAR"**.
6. **Paso 4 del asistente: "Resumen":**
   * Revisa que todo esté correcto y haz clic en **"VOLVER AL PANEL"** al final de la página.

---

## Paso 3: Crear las Credenciales OAuth 2.0 (Client ID y Client Secret)

1. En el submenú lateral izquierdo (dentro de *APIs y servicios*), haz clic en:  
   👉 **Credenciales** (Credentials).
2. En la parte superior, haz clic en: **"+ CREAR CREDENCIALES"** > **"ID de cliente de OAuth"**.
3. Completa el formulario de credenciales:
   * **Tipo de aplicación:** Selecciona **"Aplicación web"** (Web application).
   * **Nombre:** `FOBANDOR Web Local` (nombre descriptivo interno).
   * **Orígenes autorizados de JavaScript:**
     * Haz clic en **"+ AGREGAR URI"**.
     * Escribe: `http://localhost:8000`
   * **URIs de redireccionamiento autorizados (MUY IMPORTANTE):**
     * Haz clic en **"+ AGREGAR URI"**.
     * Escribe exactamente la siguiente URL:  
       `http://localhost:8000/accounts/google/login/callback/`
     * > ⚠️ **Atención:** Debe incluir la barra `/` final. Si omites la barra final, Google rechazará la conexión con un error `redirect_uri_mismatch`.
4. Haz clic en el botón azul: **"CREAR"**.
5. Se abrirá una ventana emergente titulada **"Cliente de OAuth creado"**:
   * Copia tu **ID de cliente** (es una cadena larga que termina en `.apps.googleusercontent.com`).
   * Copia tu **Secreto del cliente** (una clave alfanumérica secreta).
   * *(Nota: siempre podrás volver a ver estas credenciales desde la sección "Credenciales" si las cierras).*

---

## Paso 4: Configurar las Credenciales en FOBANDOR (Archivo .env)

### 1. ¿En qué archivo y en qué ruta exacta se configuran?
El archivo se llama **`.env`** (con un punto al inicio, lo que indica que es un archivo de entorno) y se encuentra en la raíz del proyecto:
* **Ruta absoluta en tu sistema operativo:**  
  `/home/jet/proyectos_lnx/proyectos/fobandor/.env`
* *(Nota sobre Linux Ubuntu: los archivos que comienzan con un punto son considerados ocultos por el sistema de archivos. Si navegas con el gestor visual de carpetas de Ubuntu, presiona la combinación de teclas `Ctrl + H` para hacerlos visibles. En tu IDE o terminal siempre es accesible).*

---

### 2. ¿En qué líneas exactas del archivo `.env` se pegan?
Abre el archivo `.env` con tu editor de texto o IDE. Ve directamente a las **líneas 13 a 15**, donde encontrarás la sección dedicada a Google OAuth:

#### ❌ Cómo está actualmente (valores de ejemplo / placeholders):
```env
# Google OAuth 2.0 (Social Login Gmail)
GOOGLE_OAUTH_CLIENT_ID=placeholder_client_id.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=placeholder_client_secret
```

---

### 3. ¿Cómo debes reemplazarlo con tus claves reales?
Debes borrar los textos de relleno (`placeholder_client_id...` y `placeholder_client_secret`) y pegar directamente las claves que Google Cloud te entregó en la ventana del Paso 3.5:

#### ✅ Cómo debe quedar (Ejemplo visual realista):
```env
# Google OAuth 2.0 (Social Login Gmail)
GOOGLE_OAUTH_CLIENT_ID=987654321012-abcdefghijklmnopqrstuvwxyz123456.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=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
```

> ⚠️ **Reglas críticas de formato:**
> * **NO uses comillas:** No encierres las claves entre comillas dobles (`" "`) ni simples (`' '`). Pega el valor directamente después del signo igual `=`.
> * **NO dejes espacios en blanco:** No dejes espacios antes ni después del signo `=`.
> * **Una sola línea por clave:** Cada clave debe quedar completa en su propia línea, sin saltos de línea intermedios.

---

### 4. ¿Cómo sabe el sistema FOBANDOR leer estas claves?
En el núcleo de Django (`config/settings/base.py`, líneas 100 a 104), el módulo `django-allauth` ya está programado para conectarse a estas variables del `.env` mediante `django-environ`:

```python
SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "online"},
        "APP": {
            "client_id": env("GOOGLE_OAUTH_CLIENT_ID", default=""),
            "secret": env("GOOGLE_OAUTH_CLIENT_SECRET", default=""),
            "key": "",
        },
    }
}
```

Al guardar los cambios en el archivo `.env`, las credenciales quedan inmediatamente vinculadas al sistema.

---

## Paso 5: Probar la Autenticación en Localhost

1. Asegúrate de que el contenedor de base de datos PostgreSQL esté corriendo:
   ```bash
   docker compose ps
   ```
2. Inicia el servidor de desarrollo de Django:
   ```bash
   source .venv/bin/activate
   python manage.py runserver 0.0.0.0:8000
   ```
3. Abre tu navegador web e ingresa a:  
   👉 **`http://localhost:8000/accounts/login/`**
4. Verás el botón estilizado con el logo oficial de Google: **"Continuar con Google"**.
5. Haz clic en el botón. Serás redirigido a la pantalla oficial de Google (`accounts.google.com`).
6. Inicia sesión con la cuenta Gmail que agregaste como *Usuario de prueba* en el Paso 2.5.
7. Google te mostrará la pantalla de confirmación: *"FOBANDOR quiere acceder a tu nombre y correo"*. Presiona **"Continuar"** (o *"Permitir"*).
8. **Resultado esperado:**
   * Google te redirigirá automáticamente a **`http://localhost:8000/es/mi-cuenta/`**.
   * Tu cuenta habrá sido creada en la base de datos PostgreSQL de FOBANDOR.
   * Tu usuario tendrá automáticamente el flag **`is_email_verified = True`** (sin tener que esperar correos de confirmación).

---

## Paso 6: ¿Cómo pasar a Producción más adelante? (www.fobandor.com)

Cuando el sitio web se despliegue en el VPS en `www.fobandor.com`, solo deberás realizar dos ajustes mínimos en la misma consola de Google Cloud:

1. **Agregar la URL de Producción en Credenciales:**
   * Vuelve a **APIs y servicios** > **Credenciales**.
   * Haz clic en el lápiz de edición de tus credenciales web.
   * En *Orígenes autorizados de JavaScript*, añade: `https://www.fobandor.com`
   * En *URIs de redireccionamiento autorizados*, añade:  
     `https://www.fobandor.com/accounts/google/login/callback/`
   * Guarda los cambios.
2. **Publicar la Aplicación (Pasar de "Testing" a "Producción"):**
   * Ve a **Pantalla de consentimiento de OAuth**.
   * Debajo de *"Estado de publicación"*, haz clic en el botón **"PUBLICAR LA APLICACIÓN"** (Publish App).
   * Al confirmar, cualquier persona del mundo con cualquier cuenta `@gmail.com` podrá registrarse sin necesidad de que la agregues manualmente a la lista de usuarios de prueba.
   * Como FOBANDOR solo solicita los permisos básicos (`email` y `profile`), **Google no requiere ningún proceso de auditoría o verificación formal de seguridad**. La publicación es inmediata.

---

© 2026 FOBANDOR. Documento técnico de configuración de infraestructura externa.

