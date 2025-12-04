# ⚠️ CAMBIOS TEMPORALES PARA SQLITE - REVERTIR ANTES DEL COMMIT

## 🔐 CREDENCIALES DE PRUEBA

### **Admin Users (Django Admin):**
```
Usuario: admin
Password: admin123
URL: http://127.0.0.1:8000/admin/

Usuario: adrian
Password: (pregunta al equipo)
URL: http://127.0.0.1:8000/admin/
```

### **Test Users (Aplicación):**
```
Pedro (Student):
Email: pedro@test.com
Password: test123

María (Landlord):
Email: maria@test.com
Password: test123
```

---

## 📝 SCRIPTS DE BASE DE DATOS TEMPORALES

### **Scripts creados para SQLite (SOLO desarrollo):**

1. **`fix_sqlite_report_type.py`** ⚠️ TEMPORAL
   - **Propósito**: Agregar columna `report_type` a tabla `report`
   - **Comando SQL**: `ALTER TABLE report ADD COLUMN report_type VARCHAR(30) DEFAULT 'OTHER' NOT NULL`
   - **Cuándo usarlo**: Una sola vez después de crear las tablas manualmente
   - **Eliminar antes de**: Commit final / merge a MySQL

2. **`fix_sqlite_admin_user.py`** ⚠️ TEMPORAL
   - **Propósito**: Agregar columna `user_id` a tabla `admin`
   - **Comando SQL**: `ALTER TABLE admin ADD COLUMN user_id INTEGER NULL`
   - **Cuándo usarlo**: Una sola vez para vincular Admin con User
   - **Eliminar antes de**: Commit final / merge a MySQL

3. **`create_admin_profiles.py`** ⚠️ TEMPORAL
   - **Propósito**: Crear registros Admin para todos los superusers
   - **Resultado**: Admin profiles para dropdown de reviewed_by
   - **Cuándo usarlo**: Después de ejecutar fix_sqlite_admin_user.py
   - **Eliminar antes de**: Commit final / merge a MySQL

4. **`create_tables_sqlite.py`** (si existe) ⚠️ TEMPORAL
   - **Propósito**: Crear tablas manualmente en SQLite
   - **Eliminar antes de**: Commit final / merge a MySQL

---

## 📂 ARCHIVOS MODIFICADOS TEMPORALMENTE

### 1. `inquiries/models.py`
```python
# ANTES (correcto para MySQL):
managed = False

# AHORA (temporal para SQLite):
managed = True  # Changed for SQLite development
```

**Ubicaciones:**
- Report class Meta (línea ~57)
- ListingReport class Meta (línea ~158)
- UserReport class Meta (línea ~193)

### 2. `operations/models.py`
```python
# ANTES (correcto para MySQL):
managed = False

# AHORA (temporal para SQLite):
managed = True  # Changed for SQLite development
```

**Ubicaciones:**
- Admin class Meta (línea ~20)

**⚠️ NOTA ADICIONAL**: Se agregó campo `user` a Admin model:
```python
user = models.OneToOneField(
    settings.AUTH_USER_MODEL,
    on_delete=models.CASCADE,
    null=True,
    blank=True,
    related_name='admin_profile'
)
```
Este campo ES NECESARIO para producción también (NO revertir).

---

## ✅ ANTES DE HACER COMMIT / MERGE A PRODUCCIÓN:

### **Paso 1: Eliminar scripts temporales**
```bash
rm fix_sqlite_report_type.py
rm fix_sqlite_admin_user.py
rm create_admin_profiles.py
rm create_tables_sqlite.py  # Si existe
rm REVERTIR_CAMBIOS_SQLITE.md  # Este archivo
```

### **Paso 2: Revertir managed=False**
```bash
# En inquiries/models.py (3 lugares)
managed = True  →  managed = False

# En operations/models.py (1 lugar)
managed = True  →  managed = False
```

### **Paso 3: Eliminar migraciones SQLite**
```bash
rm inquiries/migrations/0002_*.py
rm operations/migrations/0003_*.py  # Si existe
```

### **Paso 4: Verificar campo user en Admin**
⚠️ **NO REVERTIR** el campo `user` en `operations/models.py`
Este campo es necesario para producción.

### **Paso 5: En MySQL, agregar columna manualmente**
```sql
-- Si la columna user_id no existe en MySQL:
ALTER TABLE admin ADD COLUMN user_id BIGINT NULL;
ALTER TABLE admin ADD CONSTRAINT fk_admin_user 
    FOREIGN KEY (user_id) REFERENCES users_user(id) ON DELETE CASCADE;

-- Crear índice
CREATE INDEX idx_admin_user ON admin(user_id);
```

---

## 🔄 COMANDOS RÁPIDOS

### **Limpieza completa (antes de commit):**
```bash
# Eliminar scripts temporales
rm fix_sqlite_*.py create_*.py REVERTIR_CAMBIOS_SQLITE.md

# Revertir models
git checkout inquiries/models.py operations/models.py

# Eliminar migraciones SQLite
rm inquiries/migrations/0002_*.py operations/migrations/0003_*.py

# Verificar cambios
git status
```

### **Verificar que solo queden cambios correctos:**
```bash
git diff inquiries/models.py operations/models.py
```

**Debe mostrar SOLO**:
- Campo `user` agregado en Admin (operations/models.py) ✅ CORRECTO
- Campo `report_type` agregado en Report (inquiries/models.py) ✅ CORRECTO
- `managed = False` en todos los Meta ✅ CORRECTO

---

## 📊 RESUMEN

### **Archivos a ELIMINAR antes de commit:**
- ❌ `fix_sqlite_report_type.py`
- ❌ `fix_sqlite_admin_user.py`
- ❌ `create_admin_profiles.py`
- ❌ `create_tables_sqlite.py`
- ❌ `REVERTIR_CAMBIOS_SQLITE.md` (este archivo)
- ❌ `inquiries/migrations/0002_*.py`
- ❌ `operations/migrations/0003_*.py`

### **Cambios a REVERTIR:**
- ⚠️ `managed = True` → `managed = False` (4 lugares)

### **Cambios a MANTENER:**
- ✅ Campo `report_type` en Report
- ✅ Campo `user` en Admin
- ✅ Todos los cambios en views, forms, services, templates
- ✅ Bootstrap integration
- ✅ CSRF protection
- ✅ Admin registration

---

## 🎯 IMPORTANTE

**Para MySQL/Producción:**
1. El sistema usará triggers para auto-moderation
2. Los modelos deben tener `managed = False`
3. Las tablas ya existen en MySQL (creadas manualmente)
4. Solo necesitas agregar columna `user_id` a tabla `admin` en MySQL

**Para SQLite/Desarrollo:**
1. Scripts temporales ya ejecutados ✅
2. Base de datos funcional para testing ✅
3. 2 Admin profiles creados (admin y adrian) ✅
