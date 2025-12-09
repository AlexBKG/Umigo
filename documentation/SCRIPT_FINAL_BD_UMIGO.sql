-- =========================================================================
-- UMIGO - SCRIPT DE CREACIÓN DE BASE DE DATOS COMPLETO
-- Versión: 3.6 FINAL
-- Fecha: 2025-12-06
-- Base de datos: umigo
-- =========================================================================
-- PROPÓSITO: Crear base de datos completa compatible con Django AUTH_USER_MODEL
-- 
-- CAMBIOS RESPECTO A VERSIONES ANTERIORES:
-- Tablas users_user, users_student, users_landlord (sin db_table en models.py)
-- Sistema completo de Django Auth (grupos, permisos)
-- User con AbstractUser (password 128 chars, is_active, is_staff, etc.)
-- Landlord con un solo campo id_url (sin id_front_url ni id_back_url)
-- User sin campo phone
-- Landlord sin campo document_type
-- Comment con parent_comment para respuestas anidadas
-- Review agregado (modelo nuevo)
-- University agregado (modelo nuevo)
-- django_session agregado (sesiones de usuarios autenticados)
-- django_admin_log agregado (historial de acciones en admin)
-- Triggers SQL corregidos (DECLARE al inicio, CHECK constraint removido)
-- CHECK constraints agregados para listing (price, rooms, bathrooms >= 0, lat/lng rangos válidos)
-- Triggers para actualizar popularity automáticamente al crear/actualizar/eliminar reviews
-- V3.4: Triggers de reportes (auto-denuncia, admins, auto-moderación con DATE_ADD(CURDATE()))
-- =========================================================================

-- Crear base de datos si no existe
CREATE DATABASE IF NOT EXISTS umigo 
    CHARACTER SET utf8mb4 
    COLLATE utf8mb4_unicode_ci;

USE umigo;

SET FOREIGN_KEY_CHECKS = 0;
SET SQL_MODE = 'NO_AUTO_VALUE_ON_ZERO';


-- =========================================================================
-- PARTE 1: TABLAS DE DJANGO AUTH (Sistema de permisos y grupos)
-- =========================================================================

-- 1.1. django_content_type (Registro de modelos)
CREATE TABLE IF NOT EXISTS django_content_type (
    id INT AUTO_INCREMENT PRIMARY KEY,
    app_label VARCHAR(100) NOT NULL,
    model VARCHAR(100) NOT NULL,
    UNIQUE KEY django_content_type_app_label_model_unique (app_label, model)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci 
COMMENT='Registro de todos los modelos de Django';

-- 1.2. auth_permission (Permisos disponibles)
CREATE TABLE IF NOT EXISTS auth_permission (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    content_type_id INT NOT NULL,
    codename VARCHAR(100) NOT NULL,
    UNIQUE KEY auth_permission_content_type_id_codename_unique (content_type_id, codename),
    CONSTRAINT auth_permission_content_type_id_fk 
        FOREIGN KEY (content_type_id) 
        REFERENCES django_content_type(id) 
        ON DELETE CASCADE,
    INDEX auth_permission_content_type_id_idx (content_type_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Permisos: add, change, delete, view por cada modelo';

-- 1.3. auth_group (Grupos: Students, Landlords, Admins)
CREATE TABLE IF NOT EXISTS auth_group (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL UNIQUE,
    UNIQUE INDEX auth_group_name_unique (name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Grupos de usuarios: Students, Landlords, Admins';

-- 1.4. auth_group_permissions (M:M Grupos ↔ Permisos)
CREATE TABLE IF NOT EXISTS auth_group_permissions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    group_id INT NOT NULL,
    permission_id INT NOT NULL,
    UNIQUE KEY auth_group_permissions_group_id_permission_id_unique (group_id, permission_id),
    CONSTRAINT auth_group_permissions_group_id_fk 
        FOREIGN KEY (group_id) 
        REFERENCES auth_group(id) 
        ON DELETE CASCADE,
    CONSTRAINT auth_group_permissions_permission_id_fk 
        FOREIGN KEY (permission_id) 
        REFERENCES auth_permission(id) 
        ON DELETE CASCADE,
    INDEX auth_group_permissions_group_id_idx (group_id),
    INDEX auth_group_permissions_permission_id_idx (permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Asignación de permisos a grupos';


-- =========================================================================
-- PARTE 2: APP USERS (users_user, users_student, users_landlord)
-- =========================================================================

-- 2.1. users_user (AbstractUser de Django)
CREATE TABLE IF NOT EXISTS users_user (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    password VARCHAR(128) NOT NULL COMMENT 'Hash Django (bcrypt/argon2)',
    last_login DATETIME NULL COMMENT 'Última vez que inició sesión',
    is_superuser BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Acceso total al admin',
    username VARCHAR(150) NOT NULL UNIQUE COMMENT 'Username único (nombre + apellido)',
    first_name VARCHAR(150) NOT NULL COMMENT 'Nombre',
    last_name VARCHAR(150) NOT NULL COMMENT 'Apellido',
    email VARCHAR(254) NOT NULL UNIQUE COMMENT 'Email único',
    is_staff BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Puede acceder al admin Django',
    is_active BOOLEAN NOT NULL DEFAULT TRUE COMMENT 'Cuenta activa (puede iniciar sesión)',
    date_joined DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Fecha de registro',
    suspension_end_at DATE NULL COMMENT 'Fecha fin de suspensión (campo custom)',
    
    INDEX idx_users_user_username (username),
    INDEX idx_users_user_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Usuario base compatible con Django AbstractUser';

-- 2.2. users_user_groups (M:M Usuarios ↔ Grupos)
CREATE TABLE IF NOT EXISTS users_user_groups (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    group_id INT NOT NULL,
    UNIQUE KEY users_user_groups_user_id_group_id_unique (user_id, group_id),
    CONSTRAINT users_user_groups_user_id_fk 
        FOREIGN KEY (user_id) 
        REFERENCES users_user(id) 
        ON DELETE CASCADE,
    CONSTRAINT users_user_groups_group_id_fk 
        FOREIGN KEY (group_id) 
        REFERENCES auth_group(id) 
        ON DELETE CASCADE,
    INDEX users_user_groups_user_id_idx (user_id),
    INDEX users_user_groups_group_id_idx (group_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Asignación de usuarios a grupos';

-- 2.3. users_user_user_permissions (M:M Usuarios ↔ Permisos individuales)
CREATE TABLE IF NOT EXISTS users_user_user_permissions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    permission_id INT NOT NULL,
    UNIQUE KEY users_user_user_permissions_user_id_permission_id_unique (user_id, permission_id),
    CONSTRAINT users_user_user_permissions_user_id_fk 
        FOREIGN KEY (user_id) 
        REFERENCES users_user(id) 
        ON DELETE CASCADE,
    CONSTRAINT users_user_user_permissions_permission_id_fk 
        FOREIGN KEY (permission_id) 
        REFERENCES auth_permission(id) 
        ON DELETE CASCADE,
    INDEX users_user_user_permissions_user_id_idx (user_id),
    INDEX users_user_user_permissions_permission_id_idx (permission_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Permisos individuales adicionales';

-- 2.4. users_student (Estudiante)
CREATE TABLE IF NOT EXISTS users_student (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE COMMENT 'FK a users_user',
    CONSTRAINT users_student_user_id_fk 
        FOREIGN KEY (user_id) 
        REFERENCES users_user(id) 
        ON DELETE CASCADE,
    INDEX idx_users_student_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Perfil de estudiante';

-- 2.5. users_landlord (Arrendador)
CREATE TABLE IF NOT EXISTS users_landlord (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE COMMENT 'FK a users_user',
    national_id VARCHAR(20) NOT NULL COMMENT 'Número de cédula/documento',
    id_url VARCHAR(200) NOT NULL COMMENT 'URL del documento de identificación',
    CONSTRAINT users_landlord_user_id_fk 
        FOREIGN KEY (user_id) 
        REFERENCES users_user(id) 
        ON DELETE CASCADE,
    INDEX idx_users_landlord_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Perfil de arrendador (propietario)';


-- =========================================================================
-- PARTE 3: APP OPERATIONS (admin)
-- =========================================================================

-- 3.1. admin (Administrador del sistema)
CREATE TABLE IF NOT EXISTS admin (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Administrador del sistema (independiente de User)';


-- =========================================================================
-- PARTE 4: APP LISTINGS (zone, university, listing, etc.)
-- =========================================================================

-- 4.1. zone (Zonas geográficas)
CREATE TABLE IF NOT EXISTS zone (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    city VARCHAR(120) NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Zonas/barrios de ciudades';

-- 4.2. university (Universidades)
CREATE TABLE IF NOT EXISTS university (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(180) NOT NULL,
    lat DECIMAL(9,6) NOT NULL COMMENT 'Latitud',
    lng DECIMAL(9,6) NOT NULL COMMENT 'Longitud',
    city VARCHAR(120) NOT NULL,
    zone_id BIGINT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT university_zone_id_fk 
        FOREIGN KEY (zone_id) 
        REFERENCES zone(id) 
        ON DELETE CASCADE,
    INDEX idx_university_zone_id (zone_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Universidades con ubicación geográfica';

-- 4.3. listing (Publicaciones de alojamiento)
CREATE TABLE IF NOT EXISTS listing (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    owner_id BIGINT NOT NULL COMMENT 'FK a users_landlord',
    price DECIMAL(12,2) NOT NULL,
    location_text VARCHAR(255) NOT NULL,
    lat DECIMAL(9,6) NOT NULL,
    lng DECIMAL(9,6) NOT NULL,
    zone_id BIGINT NOT NULL,
    rooms INT NOT NULL,
    bathrooms INT NOT NULL,
    shared_with_people INT NOT NULL DEFAULT 0,
    utilities_price DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    available BOOLEAN NOT NULL DEFAULT FALSE COMMENT 'Requiere mínimo 1 foto para ser TRUE',
    views INT UNSIGNED NOT NULL DEFAULT 0,
    popularity FLOAT NOT NULL DEFAULT 0.0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT listing_owner_id_fk 
        FOREIGN KEY (owner_id) 
        REFERENCES users_landlord(id) 
        ON DELETE CASCADE,
    CONSTRAINT listing_zone_id_fk 
        FOREIGN KEY (zone_id) 
        REFERENCES zone(id) 
        ON DELETE RESTRICT,
    CONSTRAINT chk_listing_price_positive CHECK (price >= 0),
    CONSTRAINT chk_listing_rooms_positive CHECK (rooms > 0),
    CONSTRAINT chk_listing_bathrooms_positive CHECK (bathrooms > 0),
    CONSTRAINT chk_listing_shared_people_non_negative CHECK (shared_with_people >= 0),
    CONSTRAINT chk_listing_utilities_non_negative CHECK (utilities_price >= 0),
    CONSTRAINT chk_listing_lat_range CHECK (lat BETWEEN -90 AND 90),
    CONSTRAINT chk_listing_lng_range CHECK (lng BETWEEN -180 AND 180),
    INDEX idx_listing_owner_id (owner_id),
    INDEX idx_listing_zone_avail_pop (zone_id, available, popularity, created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Publicaciones de alojamiento';

-- 4.4. listing_photo (Fotos de listings)
CREATE TABLE IF NOT EXISTS listing_photo (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    listing_id BIGINT NOT NULL,
    url VARCHAR(300) NOT NULL,
    mime_type VARCHAR(50) NOT NULL,
    size_bytes BIGINT NOT NULL,
    sort_order SMALLINT NOT NULL DEFAULT 0,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT listing_photo_listing_id_fk 
        FOREIGN KEY (listing_id) 
        REFERENCES listing(id) 
        ON DELETE CASCADE,
    UNIQUE KEY uq_listing_photo_order (listing_id, sort_order),
    CONSTRAINT chk_listing_photo_sort_order CHECK (sort_order >= 0 AND sort_order <= 4),
    CONSTRAINT chk_listing_photo_size_bytes CHECK (size_bytes <= 524288000),
    CONSTRAINT chk_listing_photo_mime_type CHECK (mime_type IN ('image/png', 'image/jpeg', 'image/jpg')),
    INDEX idx_listing_photo_listing_id (listing_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Fotos de listings (formatos PNG/JPEG/JPG, máximo 5 por listing, 500MB cada una)';

-- 4.5. favorite (Tabla M:N explícita con modelo Django)
CREATE TABLE IF NOT EXISTS favorite (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    student_id BIGINT NOT NULL,
    listing_id BIGINT NOT NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT favorite_student_id_fk 
        FOREIGN KEY (student_id) 
        REFERENCES users_student(id) 
        ON DELETE CASCADE,
    CONSTRAINT favorite_listing_id_fk 
        FOREIGN KEY (listing_id) 
        REFERENCES listing(id) 
        ON DELETE CASCADE,
    UNIQUE KEY favorite_unique_pair (student_id, listing_id),
    INDEX ix_favorite_listing (listing_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Favoritos de estudiantes (modelo explícito con id autoincremental)';

-- 4.6. review (Reseñas de estudiantes)
CREATE TABLE IF NOT EXISTS review (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    listing_id BIGINT NOT NULL,
    student_id BIGINT NOT NULL,
    rating SMALLINT UNSIGNED NOT NULL COMMENT 'Calificación 1-5',
    text VARCHAR(800) NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT review_listing_id_fk 
        FOREIGN KEY (listing_id) 
        REFERENCES listing(id) 
        ON DELETE CASCADE,
    CONSTRAINT review_student_id_fk 
        FOREIGN KEY (student_id) 
        REFERENCES users_student(id) 
        ON DELETE CASCADE,
    UNIQUE KEY uq_review_student_listing (student_id, listing_id),
    CHECK (rating >= 1 AND rating <= 5),
    INDEX idx_review_listing_id (listing_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Reseñas de estudiantes sobre listings';

-- 4.7. comment (Comentarios con respuestas anidadas)
CREATE TABLE IF NOT EXISTS comment (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    listing_id BIGINT NOT NULL,
    author_id BIGINT NOT NULL COMMENT 'FK a users_user',
    parent_comment_id BIGINT NULL COMMENT 'Para respuestas anidadas',
    text VARCHAR(800) NOT NULL COMMENT 'Máximo 800 caracteres',
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT comment_listing_id_fk 
        FOREIGN KEY (listing_id) 
        REFERENCES listing(id) 
        ON DELETE CASCADE,
    CONSTRAINT comment_author_id_fk 
        FOREIGN KEY (author_id) 
        REFERENCES users_user(id) 
        ON DELETE CASCADE,
    CONSTRAINT comment_parent_comment_id_fk 
        FOREIGN KEY (parent_comment_id) 
        REFERENCES comment(id) 
        ON DELETE CASCADE,
    CONSTRAINT chk_comment_non_whitespace 
        CHECK (CHAR_LENGTH(TRIM(`text`)) > 0),
    INDEX idx_comment_listing_id (listing_id),
    INDEX idx_comment_parent_comment_id (parent_comment_id),
    INDEX idx_comment_author_listing (author_id, listing_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Comentarios en listings con soporte para respuestas anidadas (validación no-self-parent en trigger)';


-- =========================================================================
-- PARTE 5: APP INQUIRIES (report, listing_report, user_report)
-- =========================================================================

-- 5.1. report (Reportes/Denuncias)
CREATE TABLE IF NOT EXISTS report (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    reporter_id BIGINT NOT NULL COMMENT 'Usuario que reporta',
    reason VARCHAR(255) NOT NULL,
    status VARCHAR(12) NOT NULL DEFAULT 'UNDER_REVIEW' 
        CHECK (status IN ('UNDER_REVIEW', 'ACCEPTED', 'REJECTED')),
    reviewed_by BIGINT NULL COMMENT 'Admin que revisó',
    reviewed_at DATETIME NULL,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT report_reporter_id_fk 
        FOREIGN KEY (reporter_id) 
        REFERENCES users_user(id) 
        ON DELETE CASCADE,
    CONSTRAINT report_reviewed_by_fk 
        FOREIGN KEY (reviewed_by) 
        REFERENCES admin(id) 
        ON DELETE SET NULL,
    INDEX idx_report_reporter_id (reporter_id),
    INDEX idx_report_status (status),
    INDEX idx_report_reviewed_by (reviewed_by)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Sistema de reportes (usuarios o listings)';

-- 5.2. listing_report (Reportes de listings)
CREATE TABLE IF NOT EXISTS listing_report (
    report_id BIGINT PRIMARY KEY,
    listing_id BIGINT NOT NULL,
    CONSTRAINT listing_report_report_id_fk 
        FOREIGN KEY (report_id) 
        REFERENCES report(id) 
        ON DELETE CASCADE,
    CONSTRAINT listing_report_listing_id_fk 
        FOREIGN KEY (listing_id) 
        REFERENCES listing(id) 
        ON DELETE CASCADE,
    INDEX idx_listing_report_listing_id (listing_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Reportes contra listings';

-- 5.3. user_report (Reportes de usuarios)
CREATE TABLE IF NOT EXISTS user_report (
    report_id BIGINT PRIMARY KEY,
    reported_user_id BIGINT NOT NULL,
    CONSTRAINT user_report_report_id_fk 
        FOREIGN KEY (report_id) 
        REFERENCES report(id) 
        ON DELETE CASCADE,
    CONSTRAINT user_report_reported_user_id_fk 
        FOREIGN KEY (reported_user_id) 
        REFERENCES users_user(id) 
        ON DELETE CASCADE,
    INDEX idx_user_report_reported_user_id (reported_user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Reportes contra usuarios';


-- =========================================================================
-- PARTE 6: DJANGO MIGRATIONS
-- =========================================================================

CREATE TABLE IF NOT EXISTS django_migrations (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    app VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    applied DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Control de migraciones de Django';

-- 6.2. django_session (Sistema de sesiones)
CREATE TABLE IF NOT EXISTS django_session (
    session_key VARCHAR(40) NOT NULL PRIMARY KEY COMMENT 'Clave única de sesión (generada por Django)',
    session_data LONGTEXT NOT NULL COMMENT 'Datos de sesión serializados (JSON con user_id, permisos, etc.)',
    expire_date DATETIME(6) NOT NULL COMMENT 'Fecha de expiración de la sesión',
    INDEX django_session_expire_date_idx (expire_date)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Sesiones de usuarios autenticados (SESSION_ENGINE=db)';

-- 6.3. django_admin_log (Registro de acciones en el admin)
CREATE TABLE IF NOT EXISTS django_admin_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    action_time DATETIME(6) NOT NULL COMMENT 'Cuándo se realizó la acción',
    object_id LONGTEXT NULL COMMENT 'ID del objeto modificado (puede ser cualquier tipo)',
    object_repr VARCHAR(200) NOT NULL COMMENT 'Representación del objeto (ej: "Juan Pérez")',
    action_flag SMALLINT UNSIGNED NOT NULL COMMENT '1=Agregar, 2=Modificar, 3=Eliminar',
    change_message LONGTEXT NOT NULL COMMENT 'Descripción del cambio (JSON)',
    content_type_id INT NULL COMMENT 'Tipo de modelo modificado',
    user_id BIGINT NOT NULL COMMENT 'Usuario que realizó la acción',
    CONSTRAINT django_admin_log_content_type_id_fk 
        FOREIGN KEY (content_type_id) 
        REFERENCES django_content_type(id) 
        ON DELETE SET NULL,
    CONSTRAINT django_admin_log_user_id_fk 
        FOREIGN KEY (user_id) 
        REFERENCES users_user(id) 
        ON DELETE CASCADE,
    INDEX django_admin_log_content_type_id_idx (content_type_id),
    INDEX django_admin_log_user_id_idx (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
COMMENT='Historial de acciones en el admin de Django';


-- =========================================================================
-- PARTE 7: INSERTAR DATOS INICIALES
-- =========================================================================

-- 7.1. Grupos por defecto
INSERT INTO auth_group (name) VALUES 
    ('Students'),
    ('Landlords'),
    ('Admins')
ON DUPLICATE KEY UPDATE name = name;


-- =========================================================================
-- PARTE 8: TRIGGERS
-- =========================================================================

DELIMITER $$

-- Trigger 1: Limpiar suspensiones expiradas automáticamente
DROP TRIGGER IF EXISTS trg_check_suspension_on_login$$

CREATE TRIGGER trg_check_suspension_on_login
BEFORE UPDATE ON users_user
FOR EACH ROW
BEGIN
    -- Si usuario intenta iniciar sesión y su suspensión ya expiró, reactivar
    IF NEW.last_login IS NOT NULL 
       AND (OLD.last_login IS NULL OR NEW.last_login > OLD.last_login)
       AND NEW.is_active = FALSE 
       AND NEW.suspension_end_at IS NOT NULL 
       AND NEW.suspension_end_at < CURDATE() THEN
        SET NEW.is_active = TRUE;
        SET NEW.suspension_end_at = NULL;
    END IF;
END$$

-- Trigger 2: Validar mínimo 1 foto antes de marcar listing como disponible
DROP TRIGGER IF EXISTS trg_listing_require_photos$$

CREATE TRIGGER trg_listing_require_photos
BEFORE UPDATE ON listing
FOR EACH ROW
BEGIN
    DECLARE photo_count INT;
    
    -- Solo validar si se está cambiando a available=TRUE
    IF NEW.available = TRUE AND OLD.available = FALSE THEN
        SELECT COUNT(*) INTO photo_count 
        FROM listing_photo 
        WHERE listing_id = NEW.id;
        
        IF photo_count < 1 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Un listing debe tener al menos 1 foto para estar disponible';
        END IF;
        
        IF photo_count > 5 THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Un listing no puede tener más de 5 fotos';
        END IF;
    END IF;
END$$

-- Trigger 3: Validar XOR en reportes (solo User O Listing, nunca ambos)
DROP TRIGGER IF EXISTS trg_report_xor_user_report$$
DROP TRIGGER IF EXISTS trg_report_xor_listing_report$$

CREATE TRIGGER trg_report_xor_user_report
BEFORE INSERT ON user_report
FOR EACH ROW
BEGIN
    IF EXISTS (SELECT 1 FROM listing_report WHERE report_id = NEW.report_id) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Un reporte no puede apuntar a un usuario Y a un listing simultáneamente';
    END IF;
END$$

CREATE TRIGGER trg_report_xor_listing_report
BEFORE INSERT ON listing_report
FOR EACH ROW
BEGIN
    IF EXISTS (SELECT 1 FROM user_report WHERE report_id = NEW.report_id) THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Un reporte no puede apuntar a un listing Y a un usuario simultáneamente';
    END IF;
END$$

-- Trigger 4: Validar que el parent comment sea del mismo listing (INSERT)
DROP TRIGGER IF EXISTS trg_comment_same_listing_bi$$

CREATE TRIGGER trg_comment_same_listing_bi
BEFORE INSERT ON comment
FOR EACH ROW
BEGIN
    DECLARE v_parent_listing BIGINT;

    IF NEW.parent_comment_id IS NOT NULL THEN
        SELECT listing_id
          INTO v_parent_listing
          FROM comment
         WHERE id = NEW.parent_comment_id;

        IF v_parent_listing IS NULL THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Parent comment does not exist';
        ELSEIF v_parent_listing <> NEW.listing_id THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Reply must belong to the same listing as its parent';
        END IF;
    END IF;
END$$

-- Trigger 5: Validar parent comment en mismo listing y no auto-referencia (UPDATE)
DROP TRIGGER IF EXISTS trg_comment_same_listing_bu$$

CREATE TRIGGER trg_comment_same_listing_bu
BEFORE UPDATE ON comment
FOR EACH ROW
BEGIN
    DECLARE v_parent_listing BIGINT;

    IF NEW.parent_comment_id IS NOT NULL THEN
        IF NEW.parent_comment_id = NEW.id THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'A comment cannot be its own parent';
        END IF;

        SELECT listing_id
          INTO v_parent_listing
          FROM comment
         WHERE id = NEW.parent_comment_id;

        IF v_parent_listing IS NULL THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Parent comment does not exist';
        ELSEIF v_parent_listing <> NEW.listing_id THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'Reply must belong to the same listing as its parent';
        END IF;
    END IF;
END$$

-- Trigger 6: Actualizar popularity cuando se INSERTA una review
DROP TRIGGER IF EXISTS trg_review_insert_update_popularity$$
CREATE TRIGGER trg_review_insert_update_popularity
AFTER INSERT ON review
FOR EACH ROW
BEGIN
    DECLARE avg_rating_val FLOAT;
    
    -- Calcular promedio de ratings
    SELECT AVG(rating)
    INTO avg_rating_val
    FROM review 
    WHERE listing_id = NEW.listing_id;
    
    -- Actualizar popularity: solo el promedio de ratings (escala 1-5)
    UPDATE listing 
    SET popularity = COALESCE(avg_rating_val, 0.0)
    WHERE id = NEW.listing_id;
END$$

-- Trigger 7: Actualizar popularity cuando se ACTUALIZA una review
DROP TRIGGER IF EXISTS trg_review_update_update_popularity$$
CREATE TRIGGER trg_review_update_update_popularity
AFTER UPDATE ON review
FOR EACH ROW
BEGIN
    DECLARE avg_rating_val FLOAT;
    
    -- Solo actualizar si cambió el rating
    IF NEW.rating != OLD.rating THEN
        SELECT AVG(rating)
        INTO avg_rating_val
        FROM review 
        WHERE listing_id = NEW.listing_id;
        
        UPDATE listing 
        SET popularity = COALESCE(avg_rating_val, 0.0)
        WHERE id = NEW.listing_id;
    END IF;
END$$

-- Trigger 8: Actualizar popularity cuando se ELIMINA una review
DROP TRIGGER IF EXISTS trg_review_delete_update_popularity$$
CREATE TRIGGER trg_review_delete_update_popularity
AFTER DELETE ON review
FOR EACH ROW
BEGIN
    DECLARE avg_rating_val FLOAT;
    
    -- COALESCE maneja el caso cuando no quedan reviews (retorna 0)
    SELECT COALESCE(AVG(rating), 0.0)
    INTO avg_rating_val
    FROM review 
    WHERE listing_id = OLD.listing_id;
    
    UPDATE listing 
    SET popularity = avg_rating_val
    WHERE id = OLD.listing_id;
END$$

-- Trigger 9: Prevenir auto-denuncia (usuario no puede reportarse a sí mismo)
DROP TRIGGER IF EXISTS trg_prevent_self_report$$

CREATE TRIGGER trg_prevent_self_report 
BEFORE INSERT ON user_report
FOR EACH ROW
BEGIN
    DECLARE v_reporter_id BIGINT;
    
    SELECT reporter_id INTO v_reporter_id 
    FROM report 
    WHERE id = NEW.report_id;
    
    IF v_reporter_id = NEW.reported_user_id THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'No puedes reportarte a ti mismo';
    END IF;
END$$

-- Trigger 10: Prevenir reportar administradores
DROP TRIGGER IF EXISTS trg_prevent_admin_report$$

CREATE TRIGGER trg_prevent_admin_report
BEFORE INSERT ON user_report
FOR EACH ROW
BEGIN
    DECLARE v_is_admin BOOLEAN;
    
    SELECT (is_superuser OR is_staff) INTO v_is_admin 
    FROM users_user 
    WHERE id = NEW.reported_user_id;
    
    IF v_is_admin THEN
        SIGNAL SQLSTATE '45000' 
        SET MESSAGE_TEXT = 'No puedes reportar a un administrador';
    END IF;
END$$

-- Trigger 11: Moderación automática al aceptar reportes contra usuarios
DROP TRIGGER IF EXISTS trg_auto_moderation$$

CREATE TRIGGER trg_auto_moderation
AFTER UPDATE ON report
FOR EACH ROW
BEGIN
    DECLARE v_report_count INT;
    DECLARE v_target_user_id BIGINT;
    
    -- Solo ejecutar si el estado cambió a ACCEPTED
    IF NEW.status = 'ACCEPTED' AND OLD.status != 'ACCEPTED' THEN
        -- Obtener el usuario reportado (si es reporte de usuario)
        SELECT reported_user_id INTO v_target_user_id 
        FROM user_report 
        WHERE report_id = NEW.id;
        
        IF v_target_user_id IS NOT NULL THEN
            -- Contar reportes aceptados contra este usuario
            SELECT COUNT(*) INTO v_report_count
            FROM report r
            INNER JOIN user_report ur ON r.id = ur.report_id
            WHERE ur.reported_user_id = v_target_user_id 
            AND r.status = 'ACCEPTED';
            
            IF v_report_count = 1 THEN
                -- Primera sanción: suspensión 30 días (usar CURDATE() para tipo DATE)
                UPDATE users_user 
                SET is_active = 0, 
                    suspension_end_at = DATE_ADD(CURDATE(), INTERVAL 30 DAY)
                WHERE id = v_target_user_id;
            ELSEIF v_report_count >= 2 THEN
                -- Segunda sanción: eliminación de cuenta
                DELETE FROM users_user 
                WHERE id = v_target_user_id;
            END IF;
        END IF;
    END IF;
END$$

-- Trigger 12: Ocultar listings cuando un landlord se desactiva
DROP TRIGGER IF EXISTS trg_landlord_deactivate_hide_listings$$

CREATE TRIGGER trg_landlord_deactivate_hide_listings
AFTER UPDATE ON users_user
FOR EACH ROW
BEGIN
    /* Cuando un usuario (landlord) pasa de activo a inactivo,
       todos sus listings se marcan como NO disponibles.
       
       RAZÓN: No tiene sentido mostrar arriendos de usuarios suspendidos/inactivos.
       
       NOTA: Al reactivar al usuario (is_active 0→1), los listings NO se reactivan
       automáticamente. El landlord debe revisarlos y activarlos manualmente.
    */
    
    IF (OLD.is_active = TRUE OR OLD.is_active = 1)
       AND (NEW.is_active = FALSE OR NEW.is_active = 0) THEN
       
       -- Marcar como NO disponibles todos los listings activos de este landlord
       UPDATE listing AS l
       INNER JOIN users_landlord AS ll
               ON ll.id = l.owner_id
       SET l.available = FALSE
       WHERE ll.user_id = NEW.id
         AND l.available = TRUE;   -- Solo actualizar los que están disponibles
    END IF;
END$$

DELIMITER ;

-- =====================================================
-- 📅 EVENTO PROGRAMADO: Auto-reactivación de usuarios
-- =====================================================
-- Este evento se ejecuta diariamente para reactivar automáticamente
-- a los usuarios cuya suspensión ya expiró, sin necesidad de que
-- intenten hacer login.

-- Habilitar el programador de eventos (Event Scheduler)
SET GLOBAL event_scheduler = ON;

DELIMITER $$

DROP EVENT IF EXISTS evt_auto_unsuspend_users$$

CREATE EVENT evt_auto_unsuspend_users
ON SCHEDULE EVERY 1 DAY
STARTS CURRENT_TIMESTAMP
DO
BEGIN
    -- Reactivar usuarios cuya suspensión ya expiró
    UPDATE users_user
    SET is_active = TRUE,
        suspension_end_at = NULL
    WHERE is_active = FALSE
      AND suspension_end_at IS NOT NULL
      AND suspension_end_at < CURDATE();
END$$

DELIMITER ;


SET FOREIGN_KEY_CHECKS = 1;


-- NOTAS IMPORTANTES:
-- - Los usuarios deben registrarse a través de la app (ya tiene lógica de grupos)
-- - Students se agregan automáticamente al grupo Students
-- - Landlords se agregan al grupo Landlords tras verificación
-- - is_active=TRUE permite iniciar sesión
-- - is_active=FALSE bloquea el inicio de sesión (suspensión)
-- - Django llenará automáticamente django_content_type y auth_permission
-- - Password: Validado en Django (8-44 chars + carácter especial) via AUTH_PASSWORD_VALIDATORS
-- - Listing_photo: Formatos PNG, JPEG, JPG permitidos (CHECK constraint chk_listing_photo_mime_type)
-- - Comment: Máximo 800 caracteres, no vacío (CHECK), padre en mismo listing (triggers)
-- - Listing: DEFAULT available=FALSE, requiere mínimo 1 foto para available=TRUE (trigger)
-- - Report: XOR User/Listing validado por triggers
-- - Zone: ON DELETE RESTRICT (protege contra borrado accidental de listings)
-- - Comment anidados: Validación de mismo listing, no auto-referencia, CASCADE en DELETE
-- - Popularity: Actualizado automáticamente por triggers al crear/actualizar/eliminar reviews
--   Fórmula: AVG(rating) - Promedio simple de ratings (escala 1-5)
-- - Auto-moderación: Triggers previenen auto-denuncia, reportar admins, y aplican sanciones automáticas
--   · 1er reporte ACEPTADO → Suspensión 30 días (is_active=0, suspension_end_at)
--   · 2+ reportes ACEPTADOS → Eliminación de cuenta
-- - suspension_end_at: Campo DATE (usa CURDATE() en triggers, timezone.now().date() en Django)

-- =========================================================================
-- 🔧 PARTE ADICIONAL: FIXES CRÍTICOS POST-CREACIÓN (v3.4 → v3.5)
-- =========================================================================
-- Fecha agregada: 2025-12-05
-- Propósito: Ajustes necesarios para compatibilidad completa con Django
-- Ejecutar DESPUÉS de crear la base de datos inicial

-- -------------------------------------------------------------------------
-- FIX 1: Agregar admin.user_id (CRÍTICO para auto-asignación de reviewed_by)
-- -------------------------------------------------------------------------
-- Problema: Django Admin model tiene OneToOneField(User) pero BD no tiene user_id
-- Impacto: inquiries/admin.py no puede auto-asignar reviewer al aceptar/rechazar reportes
-- Solución: Agregar columna user_id con FK a users_user

ALTER TABLE admin 
ADD COLUMN user_id BIGINT NULL UNIQUE 
COMMENT 'Usuario Django asociado a este admin (is_staff=TRUE o is_superuser=TRUE)';

ALTER TABLE admin
ADD CONSTRAINT admin_user_id_fk 
    FOREIGN KEY (user_id) REFERENCES users_user(id) 
    ON DELETE SET NULL;

CREATE INDEX idx_admin_user_id ON admin(user_id);

-- Script opcional para vincular admins existentes con superusers:
-- UPDATE admin a
-- INNER JOIN users_user u ON u.is_superuser = TRUE
-- SET a.user_id = u.id
-- WHERE a.user_id IS NULL
-- LIMIT 1;

-- -------------------------------------------------------------------------
-- FIX 2: Agregar UNIQUE constraint en review (MEDIO - Regla de negocio)
-- -------------------------------------------------------------------------
-- Problema: Regla "1 review por student/listing" no implementada
-- Impacto: Un student puede hacer múltiples reviews del mismo listing
-- Solución: Agregar constraint UNIQUE(student_id, listing_id)

-- Eliminar duplicados si existen (ejecutar SOLO si hay datos):
-- DELETE r1 FROM review r1
-- INNER JOIN review r2 
-- WHERE r1.id > r2.id 
--   AND r1.student_id = r2.student_id 
--   AND r1.listing_id = r2.listing_id;

ALTER TABLE review 
ADD CONSTRAINT unique_student_listing 
UNIQUE (student_id, listing_id)
COMMENT '1 review por student/listing (regla de negocio)';

-- =========================================================================
-- ✅ VERIFICACIÓN POST-MIGRACIÓN
-- =========================================================================

-- Verificar que admin.user_id existe
SELECT 
    COLUMN_NAME, 
    DATA_TYPE, 
    IS_NULLABLE, 
    COLUMN_KEY,
    COLUMN_COMMENT
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_SCHEMA = 'umigo' 
  AND TABLE_NAME = 'admin'
  AND COLUMN_NAME = 'user_id';

-- Verificar constraint UNIQUE en review
SELECT 
    CONSTRAINT_NAME,
    TABLE_NAME,
    COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'umigo'
  AND TABLE_NAME = 'review'
  AND CONSTRAINT_NAME = 'unique_student_listing';

-- Verificar FK de admin.user_id
SELECT 
    CONSTRAINT_NAME,
    TABLE_NAME,
    COLUMN_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'umigo'
  AND TABLE_NAME = 'admin'
  AND COLUMN_NAME = 'user_id'
  AND REFERENCED_TABLE_NAME IS NOT NULL;

-- =========================================================================
-- 📊 RESUMEN DE CAMBIOS v3.4 → v3.5
-- =========================================================================
-- ✅ admin.user_id agregado (BIGINT NULL UNIQUE con FK a users_user)
-- ✅ review UNIQUE(student_id, listing_id) agregado
-- ✅ Índices creados para performance
-- ✅ Django models ahora usan managed=False (no modifican estructura)
-- ✅ Triggers v3.4 se mantienen intactos y funcionales
-- ✅ Sistema completo compatible con Django + MySQL

-- NOTAS FINALES:
-- - Ejecutar este script UNA SOLA VEZ después de crear la BD inicial
-- - Si admin.user_id ya existe, comentar el ALTER TABLE correspondiente
-- - Si unique_student_listing ya existe, comentar el ALTER TABLE correspondiente
-- - Los modelos Django tienen managed=False para NO modificar estas tablas
-- - Versión final: 3.5 (compatible con reports-system-clean branch)

