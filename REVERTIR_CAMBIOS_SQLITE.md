# 📋 MIGRACIONES LIMPIAS - SISTEMA DE REPORTES

## ✅ PROBLEMA RESUELTO

**Error original:** "no such table: report" en `/admin/inquiries/report/`

**Causa:** Se crearon tablas manualmente en SQLite antes de hacer migraciones correctas de Django.

**Solución aplicada:** 
1. Se restauró la base de datos original del commit inicial (grupos y usuarios intactos)
2. Se eliminaron migraciones incorrectas con `managed=False`
3. Se crearon migraciones limpias con `managed=True` usando `makemigrations`
4. Se aplicaron con `migrate` para crear las tablas correctamente

---

## 🔐 CREDENCIALES DE TESTING (SQLite)

### **Admin Django:**
```
Usuario: admin
Password: admin123
URL: http://127.0.0.1:8000/admin/
```

### **Usuarios de la base de datos original:**
- `adrian` (superuser) - password: pregunta al equipo
- `Adrian Benavides` 
- `Jeronimo Caguazango`

---

## 📊 GRUPOS Y PERMISOS PRESERVADOS

✅ **Grupos originales del proyecto (intactos):**
- `Landlords` (ID: 1)
- `Students` (ID: 2)

✅ **Usuarios originales (intactos):**
- Adrian (superuser)
- Adrian Benavides
- Jeronimo Caguazango

---

## 📂 ESTADO ACTUAL DE MODELOS

### **Modelos con `managed = True` (para desarrollo SQLite):**

**inquiries/models.py:**
- `Report` (línea ~57)
- `ListingReport` (línea ~158)
- `UserReport` (línea ~193)

**operations/models.py:**
- `Admin` (línea ~23)

**⚠️ IMPORTANTE:** El campo `user` en `Admin` model ES NECESARIO para producción (NO revertir):
```python
user = models.OneToOneField(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    related_name='admin_profile'
)
```

---

## 🚀 MIGRACIÓN A MYSQL (PRODUCCIÓN)

### **Paso 1: Revertir `managed = True` a `managed = False`**

En los 4 modelos de reports, cambiar:
```python
# inquiries/models.py (3 lugares: Report, ListingReport, UserReport)
managed = True  →  managed = False

# operations/models.py (1 lugar: Admin)
managed = True  →  managed = False
```

### **Paso 2: Agregar campo `user_id` a tabla `admin` en MySQL**

```sql
-- Agregar columna
ALTER TABLE admin ADD COLUMN user_id BIGINT NULL;

-- Agregar foreign key
ALTER TABLE admin ADD CONSTRAINT fk_admin_user 
    FOREIGN KEY (user_id) REFERENCES users_user(id) ON DELETE CASCADE;

-- Crear índice
CREATE INDEX idx_admin_user ON admin(user_id);
```

### **Paso 3: Crear Admin profiles en MySQL**

Ejecutar script para vincular superusers existentes con Admin:
```python
from django.contrib.auth import get_user_model
from operations.models import Admin

User = get_user_model()

for user in User.objects.filter(is_superuser=True):
    Admin.objects.get_or_create(user=user)
    print(f"✓ Admin profile creado para: {user.username}")
```

### **Paso 4: Verificar que NO se apliquen migraciones de reports**

Las tablas ya existen en MySQL con los triggers v3.4. Marcar las migraciones como aplicadas sin ejecutarlas:

```bash
python manage.py migrate inquiries --fake
python manage.py migrate operations --fake
```

---

## ✅ CAMBIOS A MANTENER (NO REVERTIR)

- ✅ Campo `user` en Admin model
- ✅ Campo `report_type` en Report model  
- ✅ Todos los cambios en views, forms, services, mixins
- ✅ Templates con modals de reportes
- ✅ Bootstrap integration
- ✅ CSRF protection
- ✅ Admin registration (inquiries/admin.py, operations/admin.py)

---

## 📝 RESUMEN DE MIGRACIONES

**SQLite (desarrollo):**
- ✅ `inquiries/migrations/0001_initial.py` - Crea Report, UserReport, ListingReport
- ✅ `operations/migrations/0001_initial.py` - Crea Admin con campo user

**MySQL (producción):**
- ⚠️ Las tablas ya existen, usar `migrate --fake`
- ⚠️ Solo agregar columna `user_id` manualmente en tabla `admin`

---

## 🎯 NOTAS IMPORTANTES

1. **Para desarrollo (SQLite):** Los modelos tienen `managed=True` para que Django cree las tablas
2. **Para producción (MySQL):** Los modelos deben tener `managed=False` porque las tablas ya existen con triggers
3. **Campo `user` en Admin:** ES NECESARIO en ambos entornos para el sistema de reviewed_by
4. **Grupos y permisos:** Se preservaron correctamente del commit original
