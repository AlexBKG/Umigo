# 🧪 GUÍA COMPLETA DE PRUEBAS - Base de Datos Umigo

**Versión:** 3.6 FINAL  
**Fecha:** 6 de diciembre de 2025  
**Base de datos:** MySQL 8.0 con 23 tablas y 11 triggers

---

## 📋 TABLA DE CONTENIDOS

1. [Visión General](#visión-general)
2. [Queries de Verificación Rápida](#queries-de-verificación-rápida)
3. [Pruebas de Triggers](#pruebas-de-triggers)
4. [Pruebas de Constraints (CHECK)](#pruebas-de-constraints-check)
5. [Pruebas de Relaciones y Cascadas](#pruebas-de-relaciones-y-cascadas)
6. [Pruebas de XOR Validation](#pruebas-de-xor-validation)
7. [Pruebas de Auto-Moderación](#pruebas-de-auto-moderación)
8. [Pruebas de Integridad Referencial](#pruebas-de-integridad-referencial)
9. [Queries Completos de Verificación](#queries-completos-de-verificación)
10. [Resultados Esperados](#resultados-esperados)

---

## 1. 🎯 VISIÓN GENERAL

### Objetivo de las Pruebas

Verificar que la base de datos funciona correctamente en todos sus aspectos:
- **Triggers:** 11 triggers automáticos activos
- **Constraints:** CHECK constraints con nombres explícitos
- **Cascadas:** DELETE CASCADE funcionando correctamente
- **Validaciones:** XOR, UNIQUE, NOT NULL, FOREIGN KEY
- **Auto-moderación:** Sistema de reportes y suspensiones

### Estructura de la Base de Datos

**23 Tablas distribuidas en:**
- **Django Authentication:** 8 tablas (auth_*, django_*)
- **Sistema de Usuarios:** 5 tablas (users_*, admin)
- **Sistema de Listings:** 6 tablas (listing, listing_photo, listing_report, favorite, review, comment)
- **Sistema de Operaciones:** 3 tablas (report, user_report, university)
- **Otras:** 1 tabla (zone)

### 11 Triggers Activos

1. **trg_listing_check_photos** - Valida 1-5 fotos si available=TRUE
2. **trg_comment_check_listing** - Valida que parent y reply estén en el mismo listing
3. **trg_listing_report_xor** - Valida que solo se reporte listing O usuario (XOR)
4. **trg_user_report_xor** - Valida que solo se reporte usuario O listing (XOR)
5. **trg_user_report_no_self** - Previene auto-reportes
6. **trg_review_insert_update_popularity** - Actualiza popularidad con AVG(rating)
7. **trg_review_update_update_popularity** - Actualiza si cambia el rating
8. **trg_review_delete_update_popularity** - Recalcula al eliminar review
9. **trg_report_auto_moderation_insert** - Auto-suspensión/eliminación al aceptar reporte
10. **trg_report_auto_moderation_update** - Auto-moderación al cambiar is_accepted
11. **trg_report_prevent_reporting_admin** - Previene reportes a administradores

---

## 2. ⚡ QUERIES DE VERIFICACIÓN RÁPIDA

### Verificar que la BD existe y tiene todas las tablas

```sql
USE umigo;

-- Debe retornar 23 tablas
SELECT COUNT(*) as total_tables 
FROM information_schema.tables 
WHERE table_schema = 'umigo';

-- Lista completa de tablas
SHOW TABLES;
```

**Resultado esperado:** 23 tablas

### Verificar que los triggers existen

```sql
-- Debe retornar 11 triggers
SELECT COUNT(*) as total_triggers 
FROM information_schema.triggers 
WHERE trigger_schema = 'umigo';

-- Lista de todos los triggers
SELECT 
    trigger_name,
    event_manipulation AS event,
    event_object_table AS tabla,
    action_timing AS timing
FROM information_schema.triggers
WHERE trigger_schema = 'umigo'
ORDER BY event_object_table, event_manipulation;
```

**Resultado esperado:** 11 triggers

### Verificar CHECK constraints

```sql
-- Debe retornar múltiples constraints
SELECT 
    tc.TABLE_NAME,
    cc.CONSTRAINT_NAME,
    cc.CHECK_CLAUSE
FROM INFORMATION_SCHEMA.CHECK_CONSTRAINTS cc
INNER JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc 
    ON cc.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
WHERE cc.CONSTRAINT_SCHEMA = 'umigo'
    AND tc.TABLE_SCHEMA = 'umigo'
ORDER BY tc.TABLE_NAME, cc.CONSTRAINT_NAME;
```

**Constraints esperados:**
- `chk_listing_photo_mime_type` - solo PNG/JPEG/JPG
- `chk_listing_photo_sort_order` - entre 1 y 5
- `chk_listing_photo_size_bytes` - positivo
- `chk_listing_price_positive` - precio ≥ 0
- Y más...

### Verificar zonas cargadas

```sql
-- Debe retornar 20 zonas
SELECT COUNT(*) as total_zones FROM zone;

-- Lista de zonas
SELECT id, name, locality, city FROM zone ORDER BY id;
```

**Resultado esperado:** 20 zonas de Bogotá

---

## 3. 🔧 PRUEBAS DE TRIGGERS

### TRIGGER 1: Validación de Fotos (trg_listing_check_photos)

**Lógica:** Si `available=TRUE`, debe haber entre 1 y 5 fotos.

#### Caso 1: Crear listing available=TRUE sin fotos (debe FALLAR)

```sql
-- Insertar listing sin fotos
INSERT INTO listing (
    landlord_id, location_text, lat, lng, zone_id, price, 
    rooms, bathrooms, size_m2, available, created_at
) VALUES (
    1, 'Calle 45 #10-20', 4.6097, -74.0817, 1, 800000, 
    2, 1, 50, TRUE, NOW()
);
```

**Resultado esperado:** ERROR - "El listing debe tener entre 1 y 5 fotos"

#### Caso 2: Crear listing available=FALSE sin fotos (debe PASAR)

```sql
INSERT INTO listing (
    landlord_id, location_text, lat, lng, zone_id, price, 
    rooms, bathrooms, size_m2, available, created_at
) VALUES (
    1, 'Carrera 30 #50-10', 4.6486, -74.0577, 2, 900000, 
    3, 2, 70, FALSE, NOW()
);
```

**Resultado esperado:** OK - Listing creado

#### Caso 3: Cambiar available=TRUE con 3 fotos (debe PASAR)

```sql
-- Primero agregar 3 fotos al listing
INSERT INTO listing_photo (listing_id, url, mime_type, size_bytes, sort_order, created_at)
VALUES 
    (LAST_INSERT_ID(), 'https://example.com/1.jpg', 'image/jpeg', 2048576, 1, NOW()),
    (LAST_INSERT_ID(), 'https://example.com/2.jpg', 'image/jpeg', 1548576, 2, NOW()),
    (LAST_INSERT_ID(), 'https://example.com/3.png', 'image/png', 3048576, 3, NOW());

-- Ahora cambiar a available=TRUE
UPDATE listing SET available = TRUE WHERE id = LAST_INSERT_ID();
```

**Resultado esperado:** OK - Cambio exitoso

#### Caso 4: Eliminar fotos dejando 0 con available=TRUE (debe FALLAR)

```sql
-- Eliminar todas las fotos
DELETE FROM listing_photo WHERE listing_id = (SELECT id FROM listing WHERE available = TRUE LIMIT 1);
```

**Resultado esperado:** ERROR - "El listing debe tener entre 1 y 5 fotos"

---

### TRIGGER 2: Validación de Comentarios (trg_comment_check_listing)

**Lógica:** Un comentario reply debe estar en el mismo listing que su parent.

#### Caso 1: Reply en diferente listing (debe FALLAR)

```sql
-- Crear comentario padre en listing 1
INSERT INTO comment (student_id, listing_id, text, created_at)
VALUES (1, 1, 'Comentario original', NOW());

SET @parent_id = LAST_INSERT_ID();

-- Intentar crear reply en listing 2 (debe fallar)
INSERT INTO comment (student_id, listing_id, parent_comment_id, text, created_at)
VALUES (1, 2, @parent_id, 'Reply en diferente listing', NOW());
```

**Resultado esperado:** ERROR - "El comentario y su parent deben estar en el mismo listing"

#### Caso 2: Reply en mismo listing (debe PASAR)

```sql
-- Reply en el mismo listing
INSERT INTO comment (student_id, listing_id, parent_comment_id, text, created_at)
VALUES (1, 1, @parent_id, 'Reply en mismo listing', NOW());
```

**Resultado esperado:** OK - Reply creado

---

### TRIGGER 3 y 4: XOR Validation en Reportes

**Lógica:** Un reporte debe tener `reported_user_id` O `reported_listing_id`, nunca ambos ni ninguno.

#### Caso 1: Reporte con ambos campos (debe FALLAR)

```sql
INSERT INTO report (reporter_id, reported_user_id, reported_listing_id, reason, created_at)
VALUES (1, 2, 1, 'Reporte inválido', NOW());
```

**Resultado esperado:** ERROR - "Un reporte debe tener un usuario O un listing reportado"

#### Caso 2: Reporte sin ningún campo (debe FALLAR)

```sql
INSERT INTO report (reporter_id, reason, created_at)
VALUES (1, 'Reporte sin objetivo', NOW());
```

**Resultado esperado:** ERROR - "Un reporte debe tener un usuario O un listing reportado"

#### Caso 3: Reporte solo usuario (debe PASAR)

```sql
INSERT INTO report (reporter_id, reported_user_id, reason, created_at)
VALUES (1, 2, 'Usuario sospechoso', NOW());
```

**Resultado esperado:** OK - Reporte creado

#### Caso 4: Reporte solo listing (debe PASAR)

```sql
INSERT INTO report (reporter_id, reported_listing_id, reason, created_at)
VALUES (1, 1, 'Listing fraudulento', NOW());
```

**Resultado esperado:** OK - Reporte creado

---

### TRIGGER 5: Prevenir Auto-Reportes

**Lógica:** Un usuario no puede reportarse a sí mismo.

#### Caso 1: Auto-reporte (debe FALLAR)

```sql
INSERT INTO report (reporter_id, reported_user_id, reason, created_at)
VALUES (1, 1, 'Intentando auto-reportarme', NOW());
```

**Resultado esperado:** ERROR - "Un usuario no puede reportarse a sí mismo"

---

### TRIGGER 6, 7, 8: Cálculo de Popularidad

**Lógica:** `popularity = AVG(rating)` de todos los reviews del listing.

#### Caso 1: Insertar primer review (debe actualizar popularity)

```sql
-- Verificar popularidad inicial
SELECT id, popularity FROM listing WHERE id = 1;
-- Resultado: popularity = 0.0

-- Insertar review con rating 5
INSERT INTO review (student_id, listing_id, rating, text, created_at)
VALUES (1, 1, 5, 'Excelente lugar', NOW());

-- Verificar popularidad actualizada
SELECT id, popularity FROM listing WHERE id = 1;
-- Resultado esperado: popularity = 5.0
```

#### Caso 2: Insertar segundo review (debe promediar)

```sql
-- Insertar review con rating 3
INSERT INTO review (student_id, listing_id, rating, text, created_at)
VALUES (2, 1, 3, 'Regular', NOW());

-- Verificar popularidad promediada
SELECT id, popularity FROM listing WHERE id = 1;
-- Resultado esperado: popularity = 4.0 (promedio de 5 y 3)
```

#### Caso 3: Actualizar rating (debe recalcular)

```sql
-- Cambiar rating de 3 a 5
UPDATE review SET rating = 5 WHERE student_id = 2 AND listing_id = 1;

-- Verificar popularidad recalculada
SELECT id, popularity FROM listing WHERE id = 1;
-- Resultado esperado: popularity = 5.0 (promedio de 5 y 5)
```

#### Caso 4: Eliminar review (debe recalcular)

```sql
-- Eliminar un review
DELETE FROM review WHERE student_id = 2 AND listing_id = 1;

-- Verificar popularidad recalculada
SELECT id, popularity FROM listing WHERE id = 1;
-- Resultado esperado: popularity = 5.0 (solo queda un review con 5)
```

#### Caso 5: Eliminar último review (debe ser 0)

```sql
-- Eliminar el último review
DELETE FROM review WHERE listing_id = 1;

-- Verificar popularidad en 0
SELECT id, popularity FROM listing WHERE id = 1;
-- Resultado esperado: popularity = 0.0
```

---

### TRIGGER 9 y 10: Auto-Moderación

**Lógica:**
- **1er reporte aceptado:** Suspender por 30 días (`is_active=0`, `suspension_end_at=DATE_ADD`)
- **2do+ reporte aceptado:** Eliminar usuario CASCADE

#### Caso 1: Primer reporte aceptado (debe SUSPENDER)

```sql
-- Crear usuario de prueba
INSERT INTO users_user (username, email, password, first_name, last_name, phone_number, is_active, date_joined, last_login)
VALUES ('usuario_test', 'test@test.com', 'hashedpass', 'Test', 'User', '3001234567', TRUE, NOW(), NOW());

SET @user_test_id = LAST_INSERT_ID();

-- Crear reporte contra el usuario
INSERT INTO report (reporter_id, reported_user_id, reason, is_accepted, created_at)
VALUES (1, @user_test_id, 'Primera infracción', TRUE, NOW());

-- Verificar suspensión
SELECT id, username, is_active, suspension_end_at FROM users_user WHERE id = @user_test_id;
-- Resultado esperado: is_active=0, suspension_end_at=NOW() + 30 días
```

#### Caso 2: Segundo reporte aceptado (debe ELIMINAR)

```sql
-- Crear segundo reporte
INSERT INTO report (reporter_id, reported_user_id, reason, is_accepted, created_at)
VALUES (1, @user_test_id, 'Segunda infracción', TRUE, NOW());

-- Verificar eliminación
SELECT id, username FROM users_user WHERE id = @user_test_id;
-- Resultado esperado: 0 filas (usuario eliminado)
```

---

### TRIGGER 11: Prevenir Reportes a Admins

**Lógica:** No se puede reportar a un usuario que es admin.

#### Caso 1: Reportar a admin (debe FALLAR)

```sql
-- Crear admin
INSERT INTO users_user (username, email, password, is_active, date_joined)
VALUES ('admin_test', 'admin@test.com', 'hashedpass', TRUE, NOW());

SET @admin_id = LAST_INSERT_ID();

INSERT INTO admin (user_id, created_at) VALUES (@admin_id, NOW());

-- Intentar reportar al admin
INSERT INTO report (reporter_id, reported_user_id, reason, created_at)
VALUES (1, @admin_id, 'Intento de reportar admin', NOW());
```

**Resultado esperado:** ERROR - "No se puede reportar a un administrador"

---

## 4. ✅ PRUEBAS DE CONSTRAINTS (CHECK)

### CHECK 1: mime_type de fotos

```sql
-- Debe PASAR (JPEG)
INSERT INTO listing_photo (listing_id, url, mime_type, size_bytes, sort_order, created_at)
VALUES (1, 'test.jpg', 'image/jpeg', 1024000, 1, NOW());

-- Debe PASAR (PNG)
INSERT INTO listing_photo (listing_id, url, mime_type, size_bytes, sort_order, created_at)
VALUES (1, 'test.png', 'image/png', 2048000, 2, NOW());

-- Debe FALLAR (GIF no permitido)
INSERT INTO listing_photo (listing_id, url, mime_type, size_bytes, sort_order, created_at)
VALUES (1, 'test.gif', 'image/gif', 512000, 3, NOW());
```

### CHECK 2: sort_order entre 1 y 5

```sql
-- Debe FALLAR (sort_order = 0)
INSERT INTO listing_photo (listing_id, url, mime_type, size_bytes, sort_order, created_at)
VALUES (1, 'test.jpg', 'image/jpeg', 1024000, 0, NOW());

-- Debe FALLAR (sort_order = 6)
INSERT INTO listing_photo (listing_id, url, mime_type, size_bytes, sort_order, created_at)
VALUES (1, 'test.jpg', 'image/jpeg', 1024000, 6, NOW());

-- Debe PASAR (sort_order = 3)
INSERT INTO listing_photo (listing_id, url, mime_type, size_bytes, sort_order, created_at)
VALUES (1, 'test.jpg', 'image/jpeg', 1024000, 3, NOW());
```

### CHECK 3: size_bytes positivo

```sql
-- Debe FALLAR (negativo)
INSERT INTO listing_photo (listing_id, url, mime_type, size_bytes, sort_order, created_at)
VALUES (1, 'test.jpg', 'image/jpeg', -1024, 1, NOW());

-- Debe FALLAR (cero)
INSERT INTO listing_photo (listing_id, url, mime_type, size_bytes, sort_order, created_at)
VALUES (1, 'test.jpg', 'image/jpeg', 0, 1, NOW());
```

### CHECK 4: price positivo o cero

```sql
-- Debe PASAR (precio 0)
INSERT INTO listing (landlord_id, location_text, lat, lng, zone_id, price, rooms, bathrooms, size_m2, available, created_at)
VALUES (1, 'Test gratis', 4.6, -74.08, 1, 0, 1, 1, 30, FALSE, NOW());

-- Debe FALLAR (precio negativo)
INSERT INTO listing (landlord_id, location_text, lat, lng, zone_id, price, rooms, bathrooms, size_m2, available, created_at)
VALUES (1, 'Test negativo', 4.6, -74.08, 1, -100000, 1, 1, 30, FALSE, NOW());
```

### CHECK 5: rooms, bathrooms positivos

```sql
-- Debe FALLAR (rooms = 0)
INSERT INTO listing (landlord_id, location_text, lat, lng, zone_id, price, rooms, bathrooms, size_m2, available, created_at)
VALUES (1, 'Test', 4.6, -74.08, 1, 500000, 0, 1, 30, FALSE, NOW());

-- Debe PASAR (rooms = 1)
INSERT INTO listing (landlord_id, location_text, lat, lng, zone_id, price, rooms, bathrooms, size_m2, available, created_at)
VALUES (1, 'Test', 4.6, -74.08, 1, 500000, 1, 1, 30, FALSE, NOW());
```

### CHECK 6: lat entre -90 y 90

```sql
-- Debe FALLAR (lat > 90)
INSERT INTO listing (landlord_id, location_text, lat, lng, zone_id, price, rooms, bathrooms, size_m2, available, created_at)
VALUES (1, 'Test', 100.0, -74.08, 1, 500000, 1, 1, 30, FALSE, NOW());

-- Debe PASAR (lat negativa válida)
INSERT INTO listing (landlord_id, location_text, lat, lng, zone_id, price, rooms, bathrooms, size_m2, available, created_at)
VALUES (1, 'Test', -45.0, -74.08, 1, 500000, 1, 1, 30, FALSE, NOW());
```

### CHECK 7: lng entre -180 y 180

```sql
-- Debe FALLAR (lng < -180)
INSERT INTO listing (landlord_id, location_text, lat, lng, zone_id, price, rooms, bathrooms, size_m2, available, created_at)
VALUES (1, 'Test', 4.6, -200.0, 1, 500000, 1, 1, 30, FALSE, NOW());

-- Debe PASAR (lng negativa válida)
INSERT INTO listing (landlord_id, location_text, lat, lng, zone_id, price, rooms, bathrooms, size_m2, available, created_at)
VALUES (1, 'Test', 4.6, -120.0, 1, 500000, 1, 1, 30, FALSE, NOW());
```

---

## 5. 🔗 PRUEBAS DE RELACIONES Y CASCADAS

### CASCADE 1: Eliminar usuario elimina su student/landlord

```sql
-- Crear usuario estudiante
INSERT INTO users_user (username, email, password, is_active, date_joined)
VALUES ('test_cascade', 'cascade@test.com', 'pass', TRUE, NOW());

SET @user_id = LAST_INSERT_ID();

INSERT INTO users_student (user_id, university_id, student_id_number, created_at)
VALUES (@user_id, 1, '20241234', NOW());

-- Eliminar usuario
DELETE FROM users_user WHERE id = @user_id;

-- Verificar que el student también se eliminó
SELECT * FROM users_student WHERE user_id = @user_id;
-- Resultado esperado: 0 filas
```

### CASCADE 2: Eliminar student elimina sus reviews

```sql
-- Crear student y review
INSERT INTO users_user (username, email, password, is_active, date_joined)
VALUES ('test_review', 'review@test.com', 'pass', TRUE, NOW());

SET @user_id = LAST_INSERT_ID();

INSERT INTO users_student (user_id, university_id, student_id_number, created_at)
VALUES (@user_id, 1, '20245678', NOW());

SET @student_id = LAST_INSERT_ID();

INSERT INTO review (student_id, listing_id, rating, text, created_at)
VALUES (@student_id, 1, 4, 'Test review', NOW());

-- Eliminar student
DELETE FROM users_student WHERE id = @student_id;

-- Verificar que el review se eliminó
SELECT * FROM review WHERE student_id = @student_id;
-- Resultado esperado: 0 filas
```

### CASCADE 3: Eliminar listing elimina fotos, comments, reviews, favorites

```sql
-- Crear listing con todo
INSERT INTO listing (landlord_id, location_text, lat, lng, zone_id, price, rooms, bathrooms, size_m2, available, created_at)
VALUES (1, 'Test cascade', 4.6, -74.08, 1, 500000, 2, 1, 50, FALSE, NOW());

SET @listing_id = LAST_INSERT_ID();

-- Agregar foto
INSERT INTO listing_photo (listing_id, url, mime_type, size_bytes, sort_order, created_at)
VALUES (@listing_id, 'foto.jpg', 'image/jpeg', 1024000, 1, NOW());

-- Agregar comment
INSERT INTO comment (student_id, listing_id, text, created_at)
VALUES (1, @listing_id, 'Comentario', NOW());

-- Agregar review
INSERT INTO review (student_id, listing_id, rating, text, created_at)
VALUES (1, @listing_id, 5, 'Review', NOW());

-- Agregar favorite
INSERT INTO favorite (student_id, listing_id, created_at)
VALUES (1, @listing_id, NOW());

-- Eliminar listing
DELETE FROM listing WHERE id = @listing_id;

-- Verificar cascadas
SELECT COUNT(*) FROM listing_photo WHERE listing_id = @listing_id;  -- 0
SELECT COUNT(*) FROM comment WHERE listing_id = @listing_id;        -- 0
SELECT COUNT(*) FROM review WHERE listing_id = @listing_id;         -- 0
SELECT COUNT(*) FROM favorite WHERE listing_id = @listing_id;       -- 0
```

---

## 6. ❌ PRUEBAS DE XOR VALIDATION

### XOR en Tablas Intermedias

```sql
-- user_report: debe tener report_id O listing_id (nunca ambos ni ninguno)
-- Esto es manejado por los triggers trg_user_report_xor

-- Caso 1: Ambos (debe FALLAR)
INSERT INTO user_report (user_id, report_id, listing_id)
VALUES (1, 1, 1);

-- Caso 2: Ninguno (debe FALLAR)
INSERT INTO user_report (user_id)
VALUES (1);

-- Caso 3: Solo report_id (debe PASAR)
INSERT INTO user_report (user_id, report_id)
VALUES (1, 1);

-- Caso 4: Solo listing_id (debe PASAR)
INSERT INTO user_report (user_id, listing_id)
VALUES (1, 1);
```

---

## 7. 🛡️ PRUEBAS DE AUTO-MODERACIÓN

### Escenario Completo de Moderación

```sql
-- 1. Crear usuario agresor
INSERT INTO users_user (username, email, password, is_active, date_joined)
VALUES ('agresor', 'agresor@test.com', 'pass', TRUE, NOW());
SET @agresor_id = LAST_INSERT_ID();

-- 2. Primera infracción (debe SUSPENDER)
INSERT INTO report (reporter_id, reported_user_id, reason, is_accepted, created_at)
VALUES (1, @agresor_id, 'Primera infracción', TRUE, NOW());

SELECT username, is_active, suspension_end_at 
FROM users_user 
WHERE id = @agresor_id;
-- Resultado esperado: is_active=0, suspension_end_at=NOW()+30días

-- 3. Reactivar manualmente (simular fin de suspensión)
UPDATE users_user 
SET is_active = TRUE, suspension_end_at = NULL 
WHERE id = @agresor_id;

-- 4. Segunda infracción (debe ELIMINAR)
INSERT INTO report (reporter_id, reported_user_id, reason, is_accepted, created_at)
VALUES (1, @agresor_id, 'Segunda infracción', TRUE, NOW());

SELECT COUNT(*) FROM users_user WHERE id = @agresor_id;
-- Resultado esperado: 0 (usuario eliminado)
```

---

## 8. 🔍 PRUEBAS DE INTEGRIDAD REFERENCIAL

### UNIQUE Constraints

```sql
-- Review: UNIQUE(student_id, listing_id)
INSERT INTO review (student_id, listing_id, rating, text, created_at)
VALUES (1, 1, 5, 'Primera review', NOW());

-- Debe FALLAR (duplicado)
INSERT INTO review (student_id, listing_id, rating, text, created_at)
VALUES (1, 1, 4, 'Segunda review del mismo student al mismo listing', NOW());
```

### FOREIGN KEY Constraints

```sql
-- Debe FALLAR (zone_id inexistente)
INSERT INTO listing (landlord_id, location_text, lat, lng, zone_id, price, rooms, bathrooms, size_m2, available, created_at)
VALUES (1, 'Test', 4.6, -74.08, 999, 500000, 1, 1, 30, FALSE, NOW());

-- Debe FALLAR (landlord_id inexistente)
INSERT INTO listing (landlord_id, location_text, lat, lng, zone_id, price, rooms, bathrooms, size_m2, available, created_at)
VALUES (999, 'Test', 4.6, -74.08, 1, 500000, 1, 1, 30, FALSE, NOW());
```

---

## 9. 📊 QUERIES COMPLETOS DE VERIFICACIÓN

Todos estos queries están disponibles en `documentation/queries_verificacion.sql`. Aquí se explica qué verifica cada sección:

### Sección 1: 👥 Usuarios

```sql
-- 1.1 Todos los usuarios básicos
SELECT id, username, email, first_name, last_name, is_active FROM users_user;

-- 1.2 Estudiantes con universidad
SELECT 
    s.id, u.username, u.email, s.student_id_number, 
    uni.name as university, u.is_active
FROM users_student s
INNER JOIN users_user u ON s.user_id = u.id
INNER JOIN university uni ON s.university_id = uni.id;

-- 1.3 Arrendadores
SELECT 
    l.id, u.username, u.email, l.id_url, u.is_active
FROM users_landlord l
INNER JOIN users_user u ON l.user_id = u.id;

-- 1.4 Administradores
SELECT 
    a.id, u.username, u.email, a.created_at
FROM admin a
INNER JOIN users_user u ON a.user_id = u.id;
```

**Qué verificar:**
- Todos los usuarios tienen `is_active` correcto
- Los estudiantes tienen `university_id` válido
- Los arrendadores tienen `id_url` (documentos)
- Admins están en ambas tablas (users_user y admin)

---

### Sección 2: 📍 Zonas

```sql
-- 2.1 Todas las zonas
SELECT id, name, locality, city FROM zone ORDER BY name;

-- 2.2 Conteo por ciudad
SELECT city, COUNT(*) as total_zones FROM zone GROUP BY city;
```

**Qué verificar:**
- Hay exactamente 20 zonas
- Todas son de Bogotá

---

### Sección 3: 🏠 Listings

```sql
-- 3.1 Todos los listings con arrendador y zona
SELECT 
    l.id, u.username as landlord_username, l.location_text, 
    z.name as zone_name, l.price, l.rooms, l.bathrooms, 
    l.available, l.popularity, l.created_at
FROM listing l
INNER JOIN users_landlord ld ON l.landlord_id = ld.id
INNER JOIN users_user u ON ld.user_id = u.id
INNER JOIN zone z ON l.zone_id = z.id
ORDER BY l.created_at DESC;

-- 3.2 Listings disponibles solamente
SELECT id, location_text, price, rooms, available 
FROM listing 
WHERE available = TRUE;

-- 3.3 Conteo de fotos por listing
SELECT l.id, l.location_text, COUNT(lp.id) as num_fotos
FROM listing l
LEFT JOIN listing_photo lp ON l.id = lp.listing_id
GROUP BY l.id
ORDER BY num_fotos DESC;

-- 3.4 Verificar integridad: listings available=TRUE deben tener 1-5 fotos
SELECT 
    l.id, 
    l.location_text, 
    l.available, 
    COUNT(lp.id) as num_fotos,
    CASE 
        WHEN l.available = TRUE AND (COUNT(lp.id) < 1 OR COUNT(lp.id) > 5) THEN 'FALLO'
        ELSE 'OK'
    END as estado_fotos
FROM listing l
LEFT JOIN listing_photo lp ON l.id = lp.listing_id
GROUP BY l.id
HAVING estado_fotos = 'FALLO';
```

**Qué verificar:**
- Todos los listings tienen `landlord_id` válido
- Todos tienen `zone_id` válido
- Listings con `available=TRUE` tienen entre 1 y 5 fotos
- `popularity` es un número entre 0 y 5

---

### Sección 4: 📷 Fotos

```sql
-- 4.1 Todas las fotos con listing
SELECT 
    lp.id, l.location_text as listing, lp.url, 
    lp.mime_type, lp.size_bytes, lp.sort_order
FROM listing_photo lp
INNER JOIN listing l ON lp.listing_id = l.id
ORDER BY lp.listing_id, lp.sort_order;

-- 4.2 Verificar mime_types válidos
SELECT 
    id, listing_id, mime_type,
    CASE 
        WHEN mime_type IN ('image/png', 'image/jpeg', 'image/jpg') THEN 'OK'
        ELSE 'FALLO'
    END as validacion_mime
FROM listing_photo
HAVING validacion_mime = 'FALLO';
```

**Qué verificar:**
- Todas las fotos tienen `mime_type` IN ('image/png', 'image/jpeg', 'image/jpg')
- `sort_order` está entre 1 y 5
- `size_bytes` es positivo

---

### Sección 5: ⭐ Favoritos

```sql
-- 5.1 Todos los favoritos
SELECT 
    f.id, u.username as student_username, l.location_text, 
    l.price, l.available, f.created_at
FROM favorite f
INNER JOIN users_student s ON f.student_id = s.id
INNER JOIN users_user u ON s.user_id = u.id
INNER JOIN listing l ON f.listing_id = l.id
ORDER BY f.created_at DESC;

-- 5.2 Favoritos por estudiante
SELECT 
    u.username as student, 
    COUNT(f.id) as total_favoritos,
    GROUP_CONCAT(l.location_text SEPARATOR ', ') as listings_favoritos
FROM users_student s
INNER JOIN users_user u ON s.user_id = u.id
LEFT JOIN favorite f ON s.id = f.student_id
LEFT JOIN listing l ON f.listing_id = l.id
GROUP BY s.id
ORDER BY total_favoritos DESC;

-- 5.3 Listings más favoriteados
SELECT 
    l.id, l.location_text, l.price, COUNT(f.id) as num_favoritos
FROM listing l
LEFT JOIN favorite f ON l.id = f.listing_id
GROUP BY l.id
ORDER BY num_favoritos DESC
LIMIT 10;
```

**Qué verificar:**
- Los favoritos tienen `student_id` y `listing_id` válidos
- No hay duplicados (UNIQUE constraint)

---

### Sección 6: 💬 Comentarios

```sql
-- 6.1 Todos los comentarios con estudiante y listing
SELECT 
    c.id, u.username as student, l.location_text as listing, 
    c.parent_comment_id, c.text, c.created_at
FROM comment c
INNER JOIN users_student s ON c.student_id = s.id
INNER JOIN users_user u ON s.user_id = u.id
INNER JOIN listing l ON c.listing_id = l.id
ORDER BY c.created_at DESC;

-- 6.2 Comentarios raíz (sin parent)
SELECT 
    c.id, u.username, c.text, c.created_at
FROM comment c
INNER JOIN users_student s ON c.student_id = s.id
INNER JOIN users_user u ON s.user_id = u.id
WHERE c.parent_comment_id IS NULL;

-- 6.3 Replies (con parent)
SELECT 
    c.id as reply_id, c.parent_comment_id, 
    u.username as author, c.text, c.created_at
FROM comment c
INNER JOIN users_student s ON c.student_id = s.id
INNER JOIN users_user u ON s.user_id = u.id
WHERE c.parent_comment_id IS NOT NULL;

-- 6.4 Árbol de comentarios (CTE recursivo)
WITH RECURSIVE comment_tree AS (
    -- Comentarios raíz
    SELECT 
        c.id, c.listing_id, c.student_id, c.parent_comment_id, 
        c.text, 0 as level, CAST(c.id AS CHAR(255)) as path
    FROM comment c
    WHERE c.parent_comment_id IS NULL
    
    UNION ALL
    
    -- Replies recursivos
    SELECT 
        c.id, c.listing_id, c.student_id, c.parent_comment_id, 
        c.text, ct.level + 1, CONCAT(ct.path, '->', c.id)
    FROM comment c
    INNER JOIN comment_tree ct ON c.parent_comment_id = ct.id
)
SELECT 
    ct.id, ct.level, ct.path, u.username, ct.text
FROM comment_tree ct
INNER JOIN users_student s ON ct.student_id = s.id
INNER JOIN users_user u ON s.user_id = u.id
ORDER BY ct.listing_id, ct.path;
```

**Qué verificar:**
- Todos los comments tienen `student_id` y `listing_id` válidos
- Los replies tienen `parent_comment_id` válido
- Parent y reply están en el mismo `listing_id` (trigger validation)

---

### Sección 7: ⭐ Reviews

```sql
-- 7.1 Todos los reviews con estudiante y listing
SELECT 
    r.id, u.username as student, l.location_text as listing, 
    r.rating, r.text, r.created_at
FROM review r
INNER JOIN users_student s ON r.student_id = s.id
INNER JOIN users_user u ON s.user_id = u.id
INNER JOIN listing l ON r.listing_id = l.id
ORDER BY r.created_at DESC;

-- 7.2 Promedio de rating por listing
SELECT 
    l.id, l.location_text, 
    AVG(r.rating) as avg_rating, 
    COUNT(r.id) as num_reviews,
    l.popularity
FROM listing l
LEFT JOIN review r ON l.id = r.listing_id
GROUP BY l.id
ORDER BY avg_rating DESC;

-- 7.3 Verificar que popularity = AVG(rating)
SELECT 
    l.id, l.location_text, 
    l.popularity as popularity_actual,
    COALESCE(AVG(r.rating), 0.0) as popularity_esperada,
    CASE 
        WHEN ABS(l.popularity - COALESCE(AVG(r.rating), 0.0)) < 0.01 THEN 'OK'
        ELSE 'FALLO'
    END as validacion
FROM listing l
LEFT JOIN review r ON l.id = r.listing_id
GROUP BY l.id
HAVING validacion = 'FALLO';
```

**Qué verificar:**
- Todos los reviews tienen `rating` entre 1 y 5
- UNIQUE(student_id, listing_id) se cumple
- `popularity` del listing coincide con AVG(rating)

---

### Sección 8: 🚨 Denuncias

```sql
-- 8.1 Todos los reportes
SELECT 
    r.id, 
    u1.username as reporter, 
    u2.username as reported_user,
    l.location_text as reported_listing,
    r.reason, r.is_accepted, r.created_at
FROM report r
INNER JOIN users_user u1 ON r.reporter_id = u1.id
LEFT JOIN users_user u2 ON r.reported_user_id = u2.id
LEFT JOIN listing l ON r.reported_listing_id = l.id
ORDER BY r.created_at DESC;

-- 8.2 Reportes aceptados
SELECT * FROM report WHERE is_accepted = TRUE;

-- 8.3 Reportes pendientes
SELECT * FROM report WHERE is_accepted IS NULL;

-- 8.4 Verificar XOR: debe tener reported_user_id O reported_listing_id (nunca ambos ni ninguno)
SELECT 
    id, reported_user_id, reported_listing_id,
    CASE 
        WHEN reported_user_id IS NOT NULL AND reported_listing_id IS NOT NULL THEN 'FALLO: Ambos'
        WHEN reported_user_id IS NULL AND reported_listing_id IS NULL THEN 'FALLO: Ninguno'
        ELSE 'OK'
    END as validacion_xor
FROM report
HAVING validacion_xor != 'OK';

-- 8.5 Usuarios con múltiples reportes
SELECT 
    u.id, u.username, COUNT(r.id) as num_reportes_recibidos
FROM users_user u
LEFT JOIN report r ON u.id = r.reported_user_id
GROUP BY u.id
HAVING num_reportes_recibidos > 0
ORDER BY num_reportes_recibidos DESC;
```

**Qué verificar:**
- Todos los reportes cumplen XOR validation
- Reportes aceptados activaron auto-moderación
- No hay reportes de usuarios a sí mismos
- No hay reportes a admins

---

### Sección 9: 📊 Estadísticas

```sql
-- Métricas globales
SELECT 
    (SELECT COUNT(*) FROM users_user) as total_usuarios,
    (SELECT COUNT(*) FROM users_student) as total_estudiantes,
    (SELECT COUNT(*) FROM users_landlord) as total_arrendadores,
    (SELECT COUNT(*) FROM admin) as total_admins,
    (SELECT COUNT(*) FROM zone) as total_zonas,
    (SELECT COUNT(*) FROM listing) as total_listings,
    (SELECT COUNT(*) FROM listing WHERE available = TRUE) as listings_disponibles,
    (SELECT COUNT(*) FROM listing_photo) as total_fotos,
    (SELECT COUNT(*) FROM favorite) as total_favoritos,
    (SELECT COUNT(*) FROM comment) as total_comentarios,
    (SELECT COUNT(*) FROM review) as total_reviews,
    (SELECT COUNT(*) FROM report) as total_reportes,
    (SELECT COUNT(*) FROM report WHERE is_accepted = TRUE) as reportes_aceptados,
    (SELECT COUNT(*) FROM users_user WHERE is_active = FALSE) as usuarios_suspendidos,
    (SELECT AVG(price) FROM listing) as precio_promedio,
    (SELECT AVG(popularity) FROM listing) as popularidad_promedio,
    (SELECT AVG(rating) FROM review) as rating_promedio;

-- Top 5 listings por popularidad
SELECT 
    l.id, l.location_text, l.price, l.popularity, 
    COUNT(r.id) as num_reviews
FROM listing l
LEFT JOIN review r ON l.id = r.listing_id
GROUP BY l.id
ORDER BY l.popularity DESC
LIMIT 5;
```

**Qué verificar:**
- Los conteos tienen sentido con los datos insertados
- No hay valores negativos
- Las relaciones entre tablas son coherentes

---

### Sección 10: 🔧 Triggers

```sql
-- 10.1 Lista de triggers activos
SELECT 
    trigger_name, event_manipulation, event_object_table, action_timing
FROM information_schema.triggers
WHERE trigger_schema = 'umigo'
ORDER BY event_object_table, event_manipulation;

-- 10.2 Conteo por tabla
SELECT 
    event_object_table, COUNT(*) as num_triggers
FROM information_schema.triggers
WHERE trigger_schema = 'umigo'
GROUP BY event_object_table;
```

**Qué verificar:**
- Hay exactamente 11 triggers
- Distribución: listing (1), comment (1), report (5), review (3), listing_report (1), user_report (1)

---

### Sección 11: 🧪 Queries de Prueba

```sql
-- Estos son queries comentados en el archivo para hacer pruebas adicionales
-- Ejemplo: Crear datos de prueba
/*
INSERT INTO users_user (username, email, password, first_name, last_name, is_active, date_joined)
VALUES ('test_user', 'test@test.com', 'hashedpass', 'Test', 'User', TRUE, NOW());
*/
```

---

## 10. ✅ RESULTADOS ESPERADOS

### Checklist General

- [ ] **23 tablas** creadas correctamente
- [ ] **11 triggers** activos y funcionales
- [ ] **20 zonas** cargadas (todas de Bogotá)
- [ ] **CHECK constraints** con nombres explícitos
- [ ] **Popularidad** calculada como AVG(rating)
- [ ] **XOR validation** en reportes funcionando
- [ ] **Auto-moderación:** 1er reporte=suspensión, 2do=eliminación
- [ ] **CASCADE deletes** funcionando en todas las relaciones
- [ ] **UNIQUE constraints** en reviews (student_id, listing_id)
- [ ] **Formatos de imagen** PNG/JPEG/JPG aceptados
- [ ] **Coordenadas** lat [-90, 90], lng [-180, 180] funcionando
- [ ] **Comentarios anidados** con validación de mismo listing

### Resultados por Trigger

| Trigger | Test | Resultado Esperado |
|---------|------|-------------------|
| trg_listing_check_photos | available=TRUE sin fotos | ERROR |
| trg_listing_check_photos | available=FALSE sin fotos | OK |
| trg_comment_check_listing | Reply en diferente listing | ERROR |
| trg_comment_check_listing | Reply en mismo listing | OK |
| trg_listing_report_xor | Ambos campos | ERROR |
| trg_listing_report_xor | Solo uno | OK |
| trg_user_report_xor | Ambos campos | ERROR |
| trg_user_report_xor | Solo uno | OK |
| trg_user_report_no_self | Auto-reporte | ERROR |
| trg_review_insert_update_popularity | 1er review rating=5 | popularity=5.0 |
| trg_review_insert_update_popularity | 2do review rating=3 | popularity=4.0 |
| trg_review_update_update_popularity | Cambiar rating | Recalcula AVG |
| trg_review_delete_update_popularity | Eliminar review | Recalcula AVG o 0 |
| trg_report_auto_moderation_insert | 1er reporte aceptado | Suspensión 30 días |
| trg_report_auto_moderation_insert | 2do reporte aceptado | Usuario eliminado |
| trg_report_prevent_reporting_admin | Reportar admin | ERROR |

### Resultados por CHECK Constraint

| Constraint | Test | Resultado Esperado |
|------------|------|-------------------|
| chk_listing_photo_mime_type | image/gif | ERROR |
| chk_listing_photo_mime_type | image/png | OK |
| chk_listing_photo_sort_order | 0 o 6 | ERROR |
| chk_listing_photo_sort_order | 1-5 | OK |
| chk_listing_photo_size_bytes | Negativo o 0 | ERROR |
| chk_listing_photo_size_bytes | Positivo | OK |
| chk_listing_price_positive | Negativo | ERROR |
| chk_listing_price_positive | 0 o positivo | OK |
| chk_listing_rooms_positive | 0 | ERROR |
| chk_listing_rooms_positive | Positivo | OK |
| chk_listing_bathrooms_positive | 0 | ERROR |
| chk_listing_bathrooms_positive | Positivo | OK |
| chk_listing_lat_range | < -90 o > 90 | ERROR |
| chk_listing_lat_range | Dentro del rango | OK |
| chk_listing_lng_range | < -180 o > 180 | ERROR |
| chk_listing_lng_range | Dentro del rango | OK |

---

## 📝 NOTAS FINALES

### Comandos Útiles

```sql
-- Ver errores recientes de MySQL
SHOW ERRORS;
SHOW WARNINGS;

-- Ver estructura de una tabla
DESCRIBE listing;

-- Ver definición de un trigger
SHOW CREATE TRIGGER trg_review_insert_update_popularity;

-- Ver CHECK constraints de una tabla
SELECT 
    cc.CONSTRAINT_NAME, cc.CHECK_CLAUSE
FROM INFORMATION_SCHEMA.CHECK_CONSTRAINTS cc
INNER JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS tc 
    ON cc.CONSTRAINT_NAME = tc.CONSTRAINT_NAME
WHERE cc.CONSTRAINT_SCHEMA = 'umigo' 
    AND tc.TABLE_NAME = 'listing_photo';
```

### Archivos Relacionados

- **Script SQL:** `documentation/SCRIPT_FINAL_BD_UMIGO.sql`
- **Queries de verificación:** `documentation/queries_verificacion.sql`
- **Configuración local:** `documentation/CONFIGURACION_LOCAL.md`
- **Instrucciones de recreación:** `documentation/INSTRUCCIONES_RECREAR_BD.md`

---

**Última actualización:** 6 de diciembre de 2025  
**Versión de la base de datos:** 3.6 FINAL
