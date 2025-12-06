# 🔧 CONFIGURACIÓN LOCAL - Sistema Umigo

**Versión:** 3.6 FINAL  
**Fecha:** 6 de diciembre de 2025  
**Para:** Miembros del equipo de desarrollo

---

## 📋 TABLA DE CONTENIDOS

1. [Requisitos Previos](#requisitos-previos)
2. [Instalación de MySQL](#instalación-de-mysql)
3. [Creación de la Base de Datos](#creación-de-la-base-de-datos)
4. [Configuración del Proyecto Django](#configuración-del-proyecto-django)
5. [Archivo .env](#archivo-env)
6. [Migraciones y Zona](#migraciones-y-zonas)
7. [Creación de Superusuario](#creación-de-superusuario)
8. [Ejecución del Servidor](#ejecución-del-servidor)
9. [Solución de Problemas](#solución-de-problemas)

---

## 1. 📦 REQUISITOS PREVIOS

### Software Necesario

- **Python 3.11+** (verificar con `python --version`)
- **MySQL 8.0+** (descargar de [mysql.com](https://dev.mysql.com/downloads/mysql/))
- **Git** (para clonar el repositorio)
- **Editor de código** (VS Code recomendado)

### Verificar Instalaciones

```powershell
# Verificar Python
python --version
# Salida esperada: Python 3.11.x

# Verificar pip
pip --version

# Verificar MySQL (después de instalar)
mysql --version
```

---

## 2. 🗄️ INSTALACIÓN DE MYSQL

### Windows

1. **Descargar MySQL Installer:**
   - Ir a: https://dev.mysql.com/downloads/installer/
   - Descargar: `mysql-installer-community-8.0.xx.msi`

2. **Ejecutar instalador:**
   - Elegir: **Developer Default**
   - Configurar contraseña de root (recordarla)
   - Puerto: **3306** (por defecto)

3. **Verificar instalación:**
   ```powershell
   mysql --version
   ```

### Crear usuario de base de datos

Abre **MySQL Workbench** o una terminal de MySQL:

```sql
-- Conectarse como root
mysql -u root -p

-- Crear usuario (usa tu propio nombre de usuario y contraseña)
CREATE USER 'tu_usuario'@'localhost' IDENTIFIED BY 'tu_contraseña';

-- Dar todos los privilegios
GRANT ALL PRIVILEGES ON *.* TO 'tu_usuario'@'localhost' WITH GRANT OPTION;

-- Aplicar cambios
FLUSH PRIVILEGES;

-- Salir
EXIT;
```

**Ejemplo:**
```sql
CREATE USER 'umigo_dev'@'localhost' IDENTIFIED BY 'MiPassword123!';
GRANT ALL PRIVILEGES ON *.* TO 'umigo_dev'@'localhost' WITH GRANT OPTION;
FLUSH PRIVILEGES;
```

---

## 3. 🗃️ CREACIÓN DE LA BASE DE DATOS

### Opción A: Usando MySQL Workbench (Recomendado)

1. **Abrir MySQL Workbench**
2. **Conectarse** con tu usuario (`tu_usuario` / `tu_contraseña`)
3. **Abrir el script:**
   - File → Open SQL Script
   - Seleccionar: `documentation/SCRIPT_FINAL_BD_UMIGO.sql`
4. **Ejecutar el script completo:**
   - Presionar el botón ⚡ (Execute) o `Ctrl+Shift+Enter`
   - Esperar 20-30 segundos

5. **Verificar que se creó:**
   ```sql
   SHOW DATABASES;
   -- Deberías ver 'umigo' en la lista
   
   USE umigo;
   SHOW TABLES;
   -- Deberías ver 23 tablas
   ```

### Opción B: Usando línea de comandos

```powershell
# Ir a la carpeta del proyecto
cd "ruta\a\Umigo"

# Ejecutar script
mysql -u tu_usuario -p < documentation\SCRIPT_FINAL_BD_UMIGO.sql

# Verificar
mysql -u tu_usuario -p -e "USE umigo; SHOW TABLES;"
```

### Estructura esperada

Deberías tener **23 tablas**:
- `admin`
- `auth_group`, `auth_group_permissions`, `auth_permission`
- `comment`
- `django_admin_log`, `django_content_type`, `django_migrations`, `django_session`
- `favorite`
- `listing`, `listing_photo`, `listing_report`
- `report`
- `review`
- `university`
- `user_report`
- `users_landlord`, `users_student`, `users_user`, `users_user_groups`, `users_user_user_permissions`
- `zone`

---

## 4. 🐍 CONFIGURACIÓN DEL PROYECTO DJANGO

### Clonar el repositorio

```powershell
# Clonar el proyecto
git clone https://github.com/AlexBKG/Umigo.git
cd Umigo

# Cambiar a la rama correcta
git checkout BD/django-models
```

### Crear entorno virtual

```powershell
# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Si da error de ejecución de scripts, ejecutar como Administrador:
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Instalar dependencias

```powershell
# Con el entorno virtual activado
pip install -r requirements.txt
```

**Paquetes principales:**
- Django 5.2.8
- mysqlclient (conector MySQL)
- python-decouple (para .env)
- Pillow (para imágenes)

---

## 5. 🔐 ARCHIVO .ENV

### Crear archivo .env

**IMPORTANTE:** El archivo `.env` NO está en el repositorio por seguridad. Debes crearlo manualmente.

1. En la **raíz del proyecto** (donde está `manage.py`), crear archivo `.env`
2. Copiar esta plantilla y **cambiar los valores** por los tuyos:

```env
# Configuración de Email (Gmail)
EMAIL_USER=""
EMAIL_PASSWORD=""

# Configuración de Base de Datos MySQL
DB_NAME="umigo"
DB_USER="tu_usuario"
DB_PASSWORD="tu_contraseña"
DB_HOST="localhost"
DB_PORT="3306"
```

### Ejemplo con tus credenciales

```env
# Configuración de Email
EMAIL_USER=""
EMAIL_PASSWORD=""

# Configuración de Base de Datos MySQL
DB_NAME="umigo"
DB_USER="umigo_dev"
DB_PASSWORD="MiPassword123!"
DB_HOST="localhost"
DB_PORT="3306"
```

### Verificar que funciona

Django debe leer automáticamente las variables del `.env`:

```python
# En settings.py ya está configurado:
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '3306'),
    }
}
```

---

## 6. 🔄 MIGRACIONES Y ZONAS

### Registrar migraciones (sin modificar la BD)

Como usamos `managed=False`, Django NO debe modificar las tablas. Solo registramos las migraciones:

```powershell
# Con entorno virtual activado
python manage.py migrate --fake
```

**Salida esperada:**
```
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, inquiries, listings, operations, sessions, users
Running migrations:
  Applying contenttypes.0001_initial... FAKED
  Applying contenttypes.0002_remove_content_type_name... FAKED
  ...
  Applying users.0002_alter_landlord_options_alter_student_options_and_more... FAKED
```

### Cargar zonas iniciales

```powershell
python manage.py loaddata zones.json
```

**Salida esperada:**
```
Installed 20 object(s) from 1 fixture(s)
```

**Zonas cargadas:**
- Teusaquillo - Bogotá
- Chapinero - Bogotá
- Engativá - Bogotá
- Suba - Bogotá
- Usaquén - Bogotá
- Kennedy - Bogotá
- Fontibón - Bogotá
- Antonio Nariño - Bogotá
- Puente Aranda - Bogotá
- La Candelaria - Bogotá
- Santa Fe - Bogotá
- San Cristóbal - Bogotá
- Usme - Bogotá
- Tunjuelito - Bogotá
- Bosa - Bogotá
- Ciudad Bolívar - Bogotá
- Sumapaz - Bogotá
- Rafael Uribe Uribe - Bogotá
- Barrios Unidos - Bogotá
- Los Mártires - Bogotá

---

## 7. 👤 CREACIÓN DE SUPERUSUARIO

```powershell
python manage.py createsuperuser
```

**Datos recomendados:**
- Username: `admin`
- Email: `admin@umigo.com` (o tu email)
- Password: `admin123` (o una contraseña segura)
- Password (again): `admin123`

**Salida esperada:**
```
Superuser created successfully.
```

**Acceso al admin:**
- URL: http://127.0.0.1:8000/admin/
- Usuario: `admin`
- Contraseña: `admin123`

---

## 8. 🚀 EJECUCIÓN DEL SERVIDOR

### Verificar configuración

```powershell
python manage.py check
```

**Salida esperada:**
```
System check identified no issues (0 silenced).
```

### Iniciar servidor

```powershell
python manage.py runserver
```

**Salida esperada:**
```
System check identified no issues (0 silenced).
December 06, 2025 - 15:30:00
Django version 5.2.8, using settings 'rentals_project.settings'
Starting development server at http://127.0.0.1:8000/
Quit the server with CTRL-BREAK.
```

### Acceder al sistema

- **Página principal:** http://127.0.0.1:8000/
- **Admin de Django:** http://127.0.0.1:8000/admin/
- **Registrarse como Estudiante:** http://127.0.0.1:8000/accounts/signup/student/
- **Registrarse como Arrendador:** http://127.0.0.1:8000/accounts/signup/landlord/

---

## 9. 🆘 SOLUCIÓN DE PROBLEMAS

### Error: "Can't connect to MySQL server"

**Causa:** MySQL no está corriendo o credenciales incorrectas.

**Solución:**
```powershell
# Verificar servicio de MySQL
Get-Service MySQL*

# Si está detenido, iniciarlo
Start-Service MySQL80

# Verificar conexión con MySQL Workbench
# Usar las mismas credenciales del .env
```

### Error: "Access denied for user"

**Causa:** Usuario o contraseña incorrectos en `.env`.

**Solución:**
1. Verificar credenciales en MySQL Workbench
2. Actualizar `.env` con las credenciales correctas
3. Reiniciar el servidor Django

### Error: "Table doesn't exist"

**Causa:** No ejecutaste el script SQL o falló la creación.

**Solución:**
```sql
-- En MySQL Workbench
USE umigo;
SHOW TABLES;

-- Si no hay 23 tablas, ejecutar nuevamente:
-- File → Open SQL Script → SCRIPT_FINAL_BD_UMIGO.sql
```

### Error: "You have 28 unapplied migration(s)"

**Causa:** No ejecutaste `python manage.py migrate --fake`.

**Solución:**
```powershell
python manage.py migrate --fake
```

### Error: "mysqlclient not installed"

**Causa:** No instalaste las dependencias.

**Solución:**
```powershell
pip install mysqlclient
# o
pip install -r requirements.txt
```

### Error: CSRF verification failed

**Causa:** Token CSRF expirado (normal después de login).

**Solución:**
- Recargar la página (F5)
- Volver a intentar la acción

### Error: "No such file or directory: '.env'"

**Causa:** No creaste el archivo `.env`.

**Solución:**
1. Crear archivo `.env` en la raíz del proyecto
2. Copiar las variables de configuración (ver sección 5)

---

## 📊 VERIFICACIÓN COMPLETA

Ejecuta estos comandos para verificar que todo funciona:

```powershell
# 1. Verificar sistema Django
python manage.py check

# 2. Verificar conexión a BD
python manage.py dbshell
# Dentro de MySQL:
SHOW TABLES;
EXIT;

# 3. Verificar zonas
python manage.py shell
# Dentro de Python:
from listings.models import Zone
print(Zone.objects.count())  # Debe ser 20
exit()

# 4. Iniciar servidor
python manage.py runserver
```

---

## 🎯 CHECKLIST DE CONFIGURACIÓN

Marca cada item cuando lo hayas completado:

- [ ] MySQL instalado y corriendo
- [ ] Usuario de base de datos creado
- [ ] Base de datos `umigo` creada (23 tablas)
- [ ] Repositorio clonado
- [ ] Entorno virtual creado y activado
- [ ] Dependencias instaladas (`pip install -r requirements.txt`)
- [ ] Archivo `.env` creado con tus credenciales
- [ ] Migraciones registradas (`migrate --fake`)
- [ ] Zonas cargadas (20 zonas)
- [ ] Superusuario creado
- [ ] Servidor Django corriendo sin errores
- [ ] Acceso al admin funcional

---

## 📞 CONTACTO Y SOPORTE

Si encuentras problemas que no están en esta guía:

1. **Revisar:** `documentation/PRUEBAS_BASE_DE_DATOS.md`
2. **Ejecutar:** Queries de verificación en `documentation/queries_verificacion.sql`
3. **Consultar:** Trigger y constraint documentation en `SCRIPT_FINAL_BD_UMIGO.sql`
4. **Contactar:** Al equipo en el grupo de WhatsApp

---

## 📚 ARCHIVOS DE REFERENCIA

- `documentation/SCRIPT_FINAL_BD_UMIGO.sql` - Script completo de la base de datos
- `documentation/queries_verificacion.sql` - Queries para verificar integridad
- `documentation/PRUEBAS_BASE_DE_DATOS.md` - Guía completa de pruebas
- `documentation/ANALISIS_ESTRUCTURA_TABLAS.md` - Análisis de la estructura
- `.env.example` - Plantilla del archivo .env (si existe)

---

**¡Configuración completada! 🎉**

Ahora puedes comenzar a desarrollar en tu ambiente local. Recuerda hacer `git pull` regularmente para mantener tu código actualizado.
