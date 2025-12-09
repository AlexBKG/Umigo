# 🔄 MIGRACIONES Y CAMBIOS EN MODELOS - TESTING

**Fecha:** Diciembre 8, 2025  
**Propósito:** Documentar cambios en modelos realizados para testing y gestión de migraciones

---

## ⚠️ IMPORTANTE: managed=False

**TODOS los modelos usan `managed=False`** porque:
- La base de datos se crea con `SCRIPT_FINAL_BD_UMIGO.sql`
- Django **NO** crea/modifica tablas automáticamente
- Las migraciones son **FAKE** (solo para registro, no ejecutan SQL)

---

## 📝 CAMBIOS REALIZADOS EN MODELOS

### 1. listings/models.py - Comment.clean()

**Líneas:** ~139-148

**Cambio:**
```python
def clean(self):
    """
    Validación: Un reply debe estar en el mismo listing que su parent.
    """
    super().clean()
    if self.parent and self.parent.listing != self.listing:
        raise ValidationError(
            'Un reply debe estar en el mismo listing que su comentario padre.'
        )
```

**Razón:**
- Test `test_comment_reply_different_listing_fails` requería esta validación
- Previene que un reply (respuesta) esté en diferente listing que su comentario padre
- Es validación de lógica de negocio, no de base de datos

**Impacto:**
- ✅ Solo afecta cuando se llama `comment.full_clean()` o `comment.save()` con validación
- ✅ No requiere cambios en BD (es validación Python)
- ✅ Backwards compatible (código anterior sigue funcionando)

---

### 2. users/models.py - Import ValidationError

**Línea:** 3

**Cambio:**
```python
from django.core.exceptions import ValidationError
```

**Razón:**
- Necesario para los métodos `clean()` de Student y Landlord
- Sin este import, se genera `NameError: name 'ValidationError' is not defined`

---

### 3. users/models.py - Student.clean()

**Líneas:** ~38-46

**Cambio:**
```python
def clean(self):
    """
    Validación: Un usuario no puede ser Student y Landlord simultáneamente.
    """
    super().clean()
    if hasattr(self.user, 'landlord_profile'):
        raise ValidationError(
            'Este usuario ya es un Landlord. Un usuario no puede ser Student y Landlord al mismo tiempo.'
        )
```

**Razón:**
- Test `test_user_cannot_be_both_student_and_landlord` requería esta validación
- Previene que un usuario sea Student Y Landlord al mismo tiempo (mutual exclusion)
- Es regla de negocio que no está en BD

**Impacto:**
- ✅ Solo afecta cuando se llama `student.full_clean()` o `student.save()` con validación
- ✅ No requiere cambios en BD
- ✅ Backwards compatible

---

### 4. users/models.py - Landlord.clean()

**Líneas:** ~72-80

**Cambio:**
```python
def clean(self):
    """
    Validación: Un usuario no puede ser Landlord y Student simultáneamente.
    """
    super().clean()
    if hasattr(self.user, 'student_profile'):
        raise ValidationError(
            'Este usuario ya es un Student. Un usuario no puede ser Landlord y Student al mismo tiempo.'
        )
```

**Razón:**
- Mismo test que arriba, pero desde el lado Landlord
- Mutual exclusion: Student ↔ Landlord
- Valida en ambos lados para robustez

**Impacto:**
- ✅ Solo afecta cuando se llama `landlord.full_clean()` o `landlord.save()` con validación
- ✅ No requiere cambios en BD
- ✅ Backwards compatible

---

## 🔧 GESTIÓN DE MIGRACIONES (FAKE)

### ¿Por qué migraciones fake?

Porque `managed=False` significa:
- Django registra los cambios pero **NO ejecuta SQL**
- La BD real se gestiona con `SCRIPT_FINAL_BD_UMIGO.sql`
- Las migraciones son solo para **historial y compatibilidad**

---

### Migraciones generadas

**listings/migrations/0004_favorite_alter_comment_table_alter_listing_table_and_more.py**
- Registra modelos: Comment, Listing, ListingPhoto, Review, etc.
- NO ejecuta SQL (managed=False)

**users/migrations/0003_alter_landlord_table_alter_student_table_and_more.py**
- Registra modelos: User, Student, Landlord
- NO ejecuta SQL (managed=False)

---

### Comandos ejecutados

```bash
# 1. Generar migraciones (fake, solo registro)
python manage.py makemigrations listings
python manage.py makemigrations users

# 2. Aplicar migraciones (fake, NO ejecuta SQL)
python manage.py migrate listings --fake
python manage.py migrate users --fake
```

**Resultado esperado:**
```
Operations to perform:
  Apply all migrations: listings, users
Running migrations:
  Applying listings.0004_favorite_alter_comment_table_alter_listing_table_and_more... FAKED
  Applying users.0003_alter_landlord_table_alter_student_table_and_more... FAKED
```

---

## ✅ VERIFICACIÓN DE COMPATIBILIDAD CON SCRIPT_FINAL

### Estructura de BD verificada

**Script ejecutado:** `verify_databases.py`

**Resultado:**
```
✅ Tablas en umigo: 23
✅ Tablas en test_umigo: 23
✅ Todas las tablas críticas son IDÉNTICAS
✅ RESULTADO: test_umigo es IDÉNTICA a umigo
```

**Tablas verificadas:**
- users_user, users_student, users_landlord
- admin, report, zone, listing, review
- comment, favorite, listing_photo
- inquiry, lease, operation

---

### Compatibilidad de clean() con SCRIPT_FINAL

| Modelo | Método | ¿Requiere ALTER TABLE? | Compatible con SCRIPT_FINAL |
|--------|--------|------------------------|------------------------------|
| Comment | clean() | ❌ NO | ✅ SÍ (100%) |
| Student | clean() | ❌ NO | ✅ SÍ (100%) |
| Landlord | clean() | ❌ NO | ✅ SÍ (100%) |

**Conclusión:**
- ✅ Los métodos `clean()` son **validaciones Python**, no SQL
- ✅ No requieren cambios en `SCRIPT_FINAL_BD_UMIGO.sql`
- ✅ La BD creada con el script es 100% compatible

---

## 🔄 REVERSIÓN DE CAMBIOS (SI ES NECESARIO)

### Si necesitas revertir los clean()

```bash
# 1. Revertir cambios en Git
git checkout HEAD -- listings/models.py users/models.py

# 2. Ejecutar tests
pytest tests/ -v

# Resultado: 46/48 pasando, 2 skipped
# (los 2 tests de validación volverán a ser skipped)
```

---

### Si necesitas revertir migraciones fake

```bash
# 1. Deshacer migraciones (fake)
python manage.py migrate listings 0003 --fake
python manage.py migrate users 0002 --fake

# 2. Borrar archivos de migración
rm listings/migrations/0004_*.py
rm users/migrations/0003_*.py

# 3. Verificar estado
python manage.py showmigrations
```

---

## 📊 RESUMEN DE IMPACTO

### Cambios en código Python
- ✅ 3 métodos `clean()` agregados
- ✅ 1 import agregado (`ValidationError`)
- ✅ 0 cambios en campos de modelos
- ✅ 0 cambios en Meta.db_table

### Cambios en base de datos
- ✅ 0 ALTER TABLE ejecutados
- ✅ 0 cambios en SCRIPT_FINAL_BD_UMIGO.sql
- ✅ 0 cambios en estructura de tablas

### Impacto en tests
- ✅ 48/48 tests pasando (100%)
- ✅ 0 tests skipped
- ✅ 0 tests fallando
- ✅ ~116 segundos de ejecución

---

## 🎯 PRÓXIMOS PASOS

1. ✅ Ejecutar migraciones fake (si aún no se hizo)
2. ✅ Verificar que BD test_umigo sea idéntica a umigo
3. ✅ Confirmar que 48/48 tests pasen
4. ✅ Documentar cambios en CAMBIOS_TESTING.md
5. ✅ Commit y push a GitHub

---

## 📚 REFERENCIAS

- **Modelos modificados:**
  - `listings/models.py` (Comment.clean)
  - `users/models.py` (Student.clean, Landlord.clean, import)

- **Tests relacionados:**
  - `tests/unit/test_models_comments.py::test_comment_reply_different_listing_fails`
  - `tests/unit/test_models_users.py::test_user_cannot_be_both_student_and_landlord`

- **Script de BD:**
  - `documentation/SCRIPT_FINAL_BD_UMIGO.sql` (NO modificado)

- **Documentación:**
  - `documentation/CAMBIOS_TESTING.md` (historial de cambios)
  - `documentation/TESTING.md` (documentación completa)
  - `documentation/ESTADO_ACTUAL_TESTS.md` (estado actual)
