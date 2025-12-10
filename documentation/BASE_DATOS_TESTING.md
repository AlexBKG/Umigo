# 🗄️ BASE DE DATOS DE TESTING - ARQUITECTURA TÉCNICA

## 📋 TABLA DE CONTENIDOS

1. [Concepto y Propósito](#concepto-y-propósito)
2. [Creación Automática](#creación-automática)
3. [Estructura Completa](#estructura-completa)
4. [Diferencias con BD de Producción](#diferencias-con-bd-de-producción)
5. [Ciclo de Vida](#ciclo-de-vida)
6. [Configuración Técnica](#configuración-técnica)
7. [Verificación y Mantenimiento](#verificación-y-mantenimiento)

---

## 🎯 CONCEPTO Y PROPÓSITO

### ¿Qué es test_umigo?

`test_umigo` es una **réplica completa** de la base de datos `umigo` que se usa exclusivamente para ejecutar tests automatizados.

### ¿Por qué es necesaria?

| Aspecto | BD Producción (`umigo`) | BD Testing (`test_umigo`) |
|---------|-------------------------|---------------------------|
| **Datos** | Datos reales de usuarios | Datos generados por tests |
| **Persistencia** | Permanente | Temporal (se resetea) |
| **Modificaciones** | Controladas manualmente | Automáticas en tests |
| **Riesgo** | Alto (datos críticos) | Nulo (datos ficticios) |
| **Acceso** | Django app + Admin | Solo pytest |

**Ejemplo de por qué es importante:**

```python
# ❌ SIN test_umigo (PELIGRO)
def test_delete_all_users():
    User.objects.all().delete()  # BORRA USUARIOS REALES 😱

# ✅ CON test_umigo (SEGURO)
def test_delete_all_users():
    User.objects.all().delete()  # Solo borra en test_umigo ✅
```

---

## 🛠️ CREACIÓN AUTOMÁTICA

### Proceso de Creación

Cuando ejecutas `pytest tests/` por primera vez, Django ejecuta automáticamente:

```
1. pytest tests/
   ↓
2. Django detecta: "test_umigo no existe"
   ↓
3. Django ejecuta: tests/setup_test_db.py
   ↓
4. setup_test_db.py ejecuta: SCRIPT_FINAL_BD_UMIGO.sql
   ↓
5. MySQL crea: Base de datos test_umigo con 23 tablas + 11 triggers
   ↓
6. Django ejecuta: python manage.py loaddata zones.json --database=default
   ↓
7. test_umigo tiene: 20 zonas de Bogotá cargadas
   ↓
8. pytest ejecuta: 48 tests sobre test_umigo
   ↓
9. tests PASAN ✅
```

### Script: `tests/setup_test_db.py`

```python
import os
import subprocess
from django.conf import settings
from pathlib import Path

def create_test_database():
    """
    Crea la base de datos test_umigo ejecutando el script SQL completo.
    
    Este script se ejecuta AUTOMÁTICAMENTE cuando pytest detecta que
    test_umigo no existe.
    """
    # Obtener ruta al script SQL
    sql_script = Path(__file__).parent.parent / 'documentation' / 'SCRIPT_FINAL_BD_UMIGO.sql'
    
    # Obtener credenciales de settings.py
    db_user = settings.DATABASES['default']['USER']
    db_password = settings.DATABASES['default']['PASSWORD']
    db_host = settings.DATABASES['default']['HOST']
    db_port = settings.DATABASES['default']['PORT']
    
    # Reemplazar nombre de BD umigo → test_umigo
    with open(sql_script, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Modificar CREATE DATABASE para test_umigo
    sql_content = sql_content.replace(
        "CREATE DATABASE IF NOT EXISTS umigo",
        "CREATE DATABASE IF NOT EXISTS test_umigo"
    )
    sql_content = sql_content.replace(
        "USE umigo;",
        "USE test_umigo;"
    )
    
    # Crear archivo temporal
    temp_sql = Path(__file__).parent / 'temp_test_db.sql'
    with open(temp_sql, 'w', encoding='utf-8') as f:
        f.write(sql_content)
    
    # Ejecutar script en MySQL
    command = [
        'mysql',
        f'-u{db_user}',
        f'-p{db_password}',
        f'-h{db_host}',
        f'-P{db_port}',
    ]
    
    with open(temp_sql, 'r') as f:
        subprocess.run(command, stdin=f, check=True)
    
    # Eliminar archivo temporal
    temp_sql.unlink()
    
    print("✅ Base de datos test_umigo creada exitosamente")


if __name__ == '__main__':
    create_test_database()
```

### Configuración en `conftest.py`

```python
# tests/conftest.py
import pytest
from django.core.management import call_command

@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """
    Fixture que se ejecuta UNA VEZ por sesión de pytest.
    
    Carga las 20 zonas de Bogotá en test_umigo.
    """
    with django_db_blocker.unblock():
        try:
            call_command('loaddata', 'zones.json', verbosity=0)
            print("\n✅ 20 zonas cargadas en test_umigo")
        except Exception as e:
            print(f"\n⚠️  Error cargando zonas: {e}")
```

---

## 📊 ESTRUCTURA COMPLETA

### Tablas (23 total)

#### 1. Sistema de Autenticación Django (7 tablas)

```sql
auth_group                      -- Grupos: Students, Landlords, Admins
auth_group_permissions          -- M:M Grupos ↔ Permisos
auth_permission                 -- Permisos: add, change, delete, view
django_content_type             -- Registro de modelos
django_admin_log                -- Historial de acciones en admin
django_migrations               -- Control de migraciones
django_session                  -- Sesiones de usuarios
```

#### 2. Usuarios (5 tablas)

```sql
users_user                      -- Usuario base (AbstractUser)
users_student                   -- Perfil de estudiante
users_landlord                  -- Perfil de arrendador
users_user_groups               -- M:M Users ↔ Groups
users_user_user_permissions     -- M:M Users ↔ Permissions
```

**Relaciones:**

```
users_user (1) ←→ (1) users_student
users_user (1) ←→ (1) users_landlord

Constraint: Usuario puede ser Student O Landlord, NUNCA ambos
Validación: Student.clean() y Landlord.clean()
```

#### 3. Listings (5 tablas)

```sql
zone                            -- Zonas geográficas (20 de Bogotá)
listing                         -- Publicaciones de alojamiento
listing_photo                   -- Fotos de listings (máximo 5)
review                          -- Reseñas de estudiantes
comment                         -- Comentarios anidados
```

**Relaciones:**

```
users_landlord (1) → (N) listing
listing (1) → (N) listing_photo [máximo 5]
listing (1) → (N) review [unique: student + listing]
listing (1) → (N) comment
comment (1) → (N) comment [parent → replies]
```

#### 4. Interacciones (1 tabla)

```sql
favorite                        -- M:M Listing ↔ Student (favoritos)
```

**Relación:**

```
users_student (N) ←→ (N) listing
Constraint: UNIQUE(student_id, listing_id)
```

#### 5. Reportes (3 tablas)

```sql
report                          -- Reporte base
user_report                     -- Reporte contra usuario
listing_report                  -- Reporte contra listing
```

**Relaciones:**

```
report (1) → (0..1) user_report
report (1) → (0..1) listing_report

Constraint XOR: Report apunta a UserReport O ListingReport, NUNCA ambos
Validación: Triggers trg_report_xor_*
```

#### 6. Operaciones (1 tabla)

```sql
admin                           -- Administrador del sistema
```

**Relación:**

```
users_user (1) ←→ (1) admin
admin (1) → (N) report [campo reviewed_by]
```

---

### Triggers (11 total)

#### Trigger 1: Auto-reactivación de suspensiones

```sql
CREATE TRIGGER trg_check_suspension_on_login
BEFORE UPDATE ON users_user
FOR EACH ROW
BEGIN
    IF NEW.last_login IS NOT NULL 
       AND NEW.suspension_end_at IS NOT NULL 
       AND NEW.suspension_end_at < CURDATE() THEN
        SET NEW.is_active = TRUE;
        SET NEW.suspension_end_at = NULL;
    END IF;
END;
```

**¿Qué hace?**
- Cuando usuario intenta login
- Si su suspensión ya expiró (suspension_end_at < hoy)
- Reactiva automáticamente (is_active=TRUE, suspension_end_at=NULL)

**Test que lo verifica:**
- `test_user_auto_reactivation_after_suspension_expires`

---

#### Trigger 2: Validar fotos antes de marcar disponible

```sql
CREATE TRIGGER trg_listing_require_photos
BEFORE UPDATE ON listing
FOR EACH ROW
BEGIN
    DECLARE photo_count INT;
    
    IF NEW.available = TRUE AND OLD.available = FALSE THEN
        SELECT COUNT(*) INTO photo_count FROM listing_photo WHERE listing_id = NEW.id;
        
        IF photo_count < 1 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Listing debe tener al menos 1 foto';
        END IF;
        
        IF photo_count > 5 THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Listing no puede tener más de 5 fotos';
        END IF;
    END IF;
END;
```

**¿Qué hace?**
- Cuando intentas cambiar listing a available=TRUE
- Cuenta las fotos del listing
- Si hay 0 fotos → ERROR
- Si hay >5 fotos → ERROR

**Test que lo verifica:**
- `test_listing_photo_minimum_one`
- `test_listing_photo_maximum_five`

---

#### Triggers 3-4: XOR en Reportes

```sql
-- Trigger 3: Al insertar UserReport
CREATE TRIGGER trg_report_xor_user_report
BEFORE INSERT ON user_report
FOR EACH ROW
BEGIN
    IF EXISTS (SELECT 1 FROM listing_report WHERE report_id = NEW.report_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Report no puede apuntar a User Y Listing';
    END IF;
END;

-- Trigger 4: Al insertar ListingReport
CREATE TRIGGER trg_report_xor_listing_report
BEFORE INSERT ON listing_report
FOR EACH ROW
BEGIN
    IF EXISTS (SELECT 1 FROM user_report WHERE report_id = NEW.report_id) THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Report no puede apuntar a Listing Y User';
    END IF;
END;
```

**¿Qué hace?**
- Un Report solo puede apuntar a UserReport O ListingReport
- Nunca puede apuntar a ambos (XOR = eXclusive OR)

**Test que lo verifica:**
- `test_report_xor_constraint`

---

#### Trigger 5: Validar parent comment en mismo listing

```sql
CREATE TRIGGER trg_comment_same_listing_bi
BEFORE INSERT ON comment
FOR EACH ROW
BEGIN
    DECLARE v_parent_listing BIGINT;
    
    IF NEW.parent_comment_id IS NOT NULL THEN
        SELECT listing_id INTO v_parent_listing FROM comment WHERE id = NEW.parent_comment_id;
        
        IF v_parent_listing <> NEW.listing_id THEN
            SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Reply debe estar en mismo listing';
        END IF;
    END IF;
END;
```

**¿Qué hace?**
- Cuando creas un reply (comment con parent)
- Verifica que el parent esté en el MISMO listing
- Si están en listings diferentes → ERROR

**Test que lo verifica:**
- `test_comment_reply_different_listing_fails`

---

#### Triggers 6-8: Actualizar popularidad con reviews

```sql
-- Trigger 6: Al INSERTAR review
CREATE TRIGGER trg_review_insert_update_popularity
AFTER INSERT ON review
FOR EACH ROW
BEGIN
    DECLARE avg_rating_val FLOAT;
    SELECT AVG(rating) INTO avg_rating_val FROM review WHERE listing_id = NEW.listing_id;
    UPDATE listing SET popularity = COALESCE(avg_rating_val, 0.0) WHERE id = NEW.listing_id;
END;

-- Trigger 7: Al ACTUALIZAR review
CREATE TRIGGER trg_review_update_update_popularity
AFTER UPDATE ON review
FOR EACH ROW
BEGIN
    DECLARE avg_rating_val FLOAT;
    IF NEW.rating != OLD.rating THEN
        SELECT AVG(rating) INTO avg_rating_val FROM review WHERE listing_id = NEW.listing_id;
        UPDATE listing SET popularity = COALESCE(avg_rating_val, 0.0) WHERE id = NEW.listing_id;
    END IF;
END;

-- Trigger 8: Al ELIMINAR review
CREATE TRIGGER trg_review_delete_update_popularity
AFTER DELETE ON review
FOR EACH ROW
BEGIN
    DECLARE avg_rating_val FLOAT;
    SELECT COALESCE(AVG(rating), 0.0) INTO avg_rating_val FROM review WHERE listing_id = OLD.listing_id;
    UPDATE listing SET popularity = avg_rating_val WHERE id = OLD.listing_id;
END;
```

**¿Qué hacen?**
- Cuando se crea/actualiza/elimina una review
- Recalculan el promedio de ratings del listing
- Actualizan `listing.popularity` automáticamente

**Fórmula:**
```
popularity = AVG(rating)
```

**Test que lo verifica:**
- `test_listing_popularity_calculation`

---

#### Triggers 9-10: Protección contra auto-denuncia y reportar admins

```sql
-- Trigger 9: Prevenir auto-denuncia
CREATE TRIGGER trg_prevent_self_report 
BEFORE INSERT ON user_report
FOR EACH ROW
BEGIN
    DECLARE v_reporter_id BIGINT;
    SELECT reporter_id INTO v_reporter_id FROM report WHERE id = NEW.report_id;
    
    IF v_reporter_id = NEW.reported_user_id THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No puedes reportarte a ti mismo';
    END IF;
END;

-- Trigger 10: Prevenir reportar admins
CREATE TRIGGER trg_prevent_admin_report
BEFORE INSERT ON user_report
FOR EACH ROW
BEGIN
    DECLARE v_is_admin BOOLEAN;
    SELECT (is_superuser OR is_staff) INTO v_is_admin FROM users_user WHERE id = NEW.reported_user_id;
    
    IF v_is_admin THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'No puedes reportar a un administrador';
    END IF;
END;
```

**¿Qué hacen?**
- Trigger 9: No puedes reportarte a ti mismo
- Trigger 10: No puedes reportar a un admin (is_staff=TRUE o is_superuser=TRUE)

---

#### Trigger 11: Auto-moderación (EL MÁS CRÍTICO)

```sql
CREATE TRIGGER trg_auto_moderation
AFTER UPDATE ON report
FOR EACH ROW
BEGIN
    DECLARE v_report_count INT;
    DECLARE v_target_user_id BIGINT;
    
    IF NEW.status = 'ACCEPTED' AND OLD.status != 'ACCEPTED' THEN
        SELECT reported_user_id INTO v_target_user_id FROM user_report WHERE report_id = NEW.id;
        
        IF v_target_user_id IS NOT NULL THEN
            SELECT COUNT(*) INTO v_report_count
            FROM report r
            INNER JOIN user_report ur ON r.id = ur.report_id
            WHERE ur.reported_user_id = v_target_user_id AND r.status = 'ACCEPTED';
            
            IF v_report_count = 1 THEN
                -- 1ER REPORTE ACEPTADO → Suspensión 30 días
                UPDATE users_user 
                SET is_active = 0, suspension_end_at = DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                WHERE id = v_target_user_id;
                
            ELSEIF v_report_count >= 2 THEN
                -- 2+ REPORTES ACEPTADOS → Eliminación permanente
                DELETE FROM users_user WHERE id = v_target_user_id;
            END IF;
        END IF;
    END IF;
END;
```

**¿Qué hace?**
- Cuando un Report cambia a status='ACCEPTED'
- Cuenta cuántos reportes ACEPTADOS tiene ese usuario
- **1er reporte:** Suspender 30 días (is_active=FALSE, suspension_end_at=hoy+30)
- **2º reporte:** Eliminar usuario permanentemente (DELETE FROM users_user)

**Tests que lo verifican:**
- `test_user_moderation_first_accepted_suspends_30_days`
- `test_user_moderation_second_accepted_deletes_user`

**Este trigger implementa el sistema completo de moderación automática.**

---

### Constraints (CHECK)

```sql
-- Listing
CHECK (price >= 0)
CHECK (rooms > 0)
CHECK (bathrooms > 0)
CHECK (shared_with_people >= 0)
CHECK (lat BETWEEN -90 AND 90)
CHECK (lng BETWEEN -180 AND 180)

-- ListingPhoto
CHECK (sort_order >= 0 AND sort_order <= 4)
CHECK (size_bytes <= 524288000)  -- 500MB
CHECK (mime_type IN ('image/png', 'image/jpeg', 'image/jpg'))

-- Review
CHECK (rating BETWEEN 1 AND 5)

-- Report
CHECK (status IN ('UNDER_REVIEW', 'ACCEPTED', 'REJECTED'))
```

**Tests que los verifican:**
- `test_listing_price_positive`
- `test_listing_rooms_minimum_one`
- `test_review_rating_range`

---

## 🔄 DIFERENCIAS CON BD DE PRODUCCIÓN

### Similitudes (100%)

| Aspecto | Producción | Testing |
|---------|------------|---------|
| **Tablas** | 23 | 23 |
| **Triggers** | 11 | 11 |
| **Constraints** | CHECK, UNIQUE, FK | Idénticos |
| **Índices** | Todos | Todos |
| **Zonas** | 20 de Bogotá | 20 de Bogotá |
| **Estructura** | SCRIPT_FINAL_BD_UMIGO.sql | Mismo script |

### Diferencias (Solo datos)

| Aspecto | Producción (`umigo`) | Testing (`test_umigo`) |
|---------|----------------------|------------------------|
| **Usuarios** | Usuarios reales | Generados por factories |
| **Listings** | Listings reales | Generados por factories |
| **Reviews** | Reviews reales | Generadas por factories |
| **Persistencia** | Permanente | Se resetea entre tests |
| **Tamaño** | Crece con el tiempo | Siempre pequeña |

**Conclusión:** `test_umigo` es una **copia exacta** de `umigo` en estructura, pero con datos temporales.

---

## 🔄 CICLO DE VIDA

### 1. Creación (Primera vez)

```
pytest tests/
↓
Django: "test_umigo no existe"
↓
Django ejecuta: setup_test_db.py
↓
MySQL crea: test_umigo con 23 tablas + 11 triggers
↓
Django carga: 20 zonas
↓
test_umigo lista ✅
```

### 2. Ejecución de Tests

```
pytest tests/
↓
conftest.py: django_db_setup se ejecuta (UNA VEZ por sesión)
↓
Para cada test:
  1. BEGIN TRANSACTION
  2. Crear datos con factories
  3. Ejecutar assertions
  4. ROLLBACK (descartar cambios)
↓
Siguiente test (BD limpia otra vez)
```

**Importante:** Cada test ve una BD limpia. Los cambios de un test NO afectan a otros.

### 3. Reutilización (--reuse-db)

```powershell
# Primera ejecución (crea BD)
pytest tests/

# Siguientes ejecuciones (reutiliza BD)
pytest tests/ --reuse-db
```

**Ventaja:** No recrea `test_umigo`, ahorra ~10 segundos.

**Desventaja:** Si cambiaste el schema (agregaste tabla, trigger, etc.), debes recrear:

```powershell
pytest tests/ --create-db
```

### 4. Destrucción

**Opción 1: Automática (default)**

```powershell
pytest tests/  # Al terminar, BD se conserva
```

Django NO destruye `test_umigo` por defecto (para reutilizarla).

**Opción 2: Manual**

```sql
-- En MySQL Workbench
DROP DATABASE test_umigo;
```

Próxima ejecución de pytest la recreará.

---

## ⚙️ CONFIGURACIÓN TÉCNICA

### `pytest.ini`

```ini
[pytest]
DJANGO_SETTINGS_MODULE = rentals_project.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    --reuse-db
    --nomigrations
    -v
markers =
    unit: Marca tests unitarios
    integration: Marca tests de integración
```

**Explicación:**

- `--reuse-db`: Reutiliza `test_umigo` entre ejecuciones
- `--nomigrations`: No ejecuta migraciones (usamos managed=False)
- `-v`: Output verbose (muestra cada test)
- `markers`: Permite filtrar tests por tipo

### `conftest.py` (Configuración global)

```python
@pytest.fixture(scope='session')
def django_db_setup(django_db_setup, django_db_blocker):
    """Fixture que se ejecuta UNA VEZ al inicio de la sesión."""
    with django_db_blocker.unblock():
        call_command('loaddata', 'zones.json', verbosity=0)

@pytest.fixture
def db_with_zones(db):
    """Alias para garantizar que tests usan BD con zonas."""
    return db
```

**Scope:**

- `scope='session'`: Se ejecuta 1 vez por sesión completa de pytest
- `scope='function'`: Se ejecuta antes de cada test (default)
- `scope='class'`: Se ejecuta antes de cada clase de tests

---

## ✅ VERIFICACIÓN Y MANTENIMIENTO

### Verificar que test_umigo existe

```sql
-- En MySQL Workbench
SHOW DATABASES;
-- Debe aparecer: test_umigo

USE test_umigo;
SHOW TABLES;
-- Debe mostrar 23 tablas
```

### Verificar triggers

```sql
USE test_umigo;
SHOW TRIGGERS;
-- Debe mostrar 11 triggers
```

### Verificar zonas

```sql
USE test_umigo;
SELECT COUNT(*) FROM zone;
-- Debe retornar: 20
```

### Verificar estructura completa

```python
# Script de verificación
python verify_databases.py
```

**Output esperado:**

```
✅ Tablas en umigo: 23
✅ Tablas en test_umigo: 23
✅ Triggers en umigo: 11
✅ Triggers en test_umigo: 11
✅ Zonas en umigo: 20
✅ Zonas en test_umigo: 20
✅ RESULTADO: test_umigo es IDÉNTICA a umigo
```

### Recrear test_umigo desde cero

```powershell
# Opción 1: Eliminar y dejar que pytest la recree
pytest tests/ --create-db

# Opción 2: Ejecutar script manualmente
python tests/setup_test_db.py

# Opción 3: Eliminar en MySQL y ejecutar tests
mysql -u tu_usuario -p
DROP DATABASE test_umigo;
EXIT;

pytest tests/
```

---

## 🎯 CONCLUSIÓN

`test_umigo` es una **base de datos separada e idéntica** a `umigo` que permite:

✅ **Ejecutar tests sin riesgo** (no afecta datos reales)  
✅ **Resetear automáticamente** entre tests  
✅ **Validar triggers y constraints** de MySQL  
✅ **Simular escenarios complejos** (suspensiones, eliminaciones)  
✅ **Mantener velocidad** (se reutiliza entre ejecuciones)  

**Nunca modifiques test_umigo manualmente.** Deja que Django la gestione automáticamente.
