-- ============================================================================
-- 📊 QUERIES DE VERIFICACIÓN - Sistema Umigo
-- Ejecuta estas queries en MySQL Workbench para verificar los datos
-- ============================================================================

-- ============================================================================
-- 1. 👥 USUARIOS
-- ============================================================================

-- Ver todos los usuarios
SELECT 
    id,
    username,
    email,
    first_name,
    last_name,
    is_staff,
    is_superuser,
    suspension_end_at,
    date_joined
FROM users_user
ORDER BY id;

-- Ver estudiantes con sus usuarios
SELECT 
    s.id as student_id,
    u.username,
    u.email,
    u.first_name,
    u.last_name
FROM users_student s
INNER JOIN users_user u ON s.user_id = u.id
ORDER BY s.id;

-- Ver arrendadores con sus usuarios
SELECT 
    l.id as landlord_id,
    u.username,
    u.email,
    u.first_name,
    u.last_name,
    l.national_id,
    l.id_url
FROM users_landlord l
INNER JOIN users_user u ON l.user_id = u.id
ORDER BY l.id;

-- Ver admins con sus usuarios
SELECT 
    a.id as admin_id,
    a.user_id,
    u.username,
    u.email,
    u.first_name,
    u.last_name
FROM admin a
INNER JOIN users_user u ON a.user_id = u.id
ORDER BY a.id;

-- ============================================================================
-- 2. 📍 ZONAS Y UBICACIONES
-- ============================================================================

-- Ver todas las zonas
SELECT 
    id,
    name,
    city
FROM zone
ORDER BY city, name;

-- Contar listings por zona
SELECT 
    z.name as zona,
    z.city,
    COUNT(l.id) as num_listings
FROM zone z
LEFT JOIN listing l ON l.zone_id = z.id
GROUP BY z.id, z.name, z.city
ORDER BY num_listings DESC;

-- ============================================================================
-- 3. 🏠 LISTINGS
-- ============================================================================

-- Ver todos los listings con información del dueño
SELECT 
    l.id,
    l.location_text,
    l.price,
    l.rooms,
    l.bathrooms,
    l.available,
    l.views,
    l.popularity,
    z.name as zona,
    u.username as owner_username,
    u.first_name as owner_name,
    (SELECT COUNT(*) FROM listing_photo WHERE listing_id = l.id) as num_fotos,
    l.created_at
FROM listing l
INNER JOIN users_landlord landlord ON l.owner_id = landlord.id
INNER JOIN users_user u ON landlord.user_id = u.id
INNER JOIN zone z ON l.zone_id = z.id
ORDER BY l.id;

-- Listings disponibles (deben tener entre 1-5 fotos)
SELECT 
    l.id,
    l.location_text,
    l.price,
    l.available,
    COUNT(lp.id) as num_fotos
FROM listing l
LEFT JOIN listing_photo lp ON lp.listing_id = l.id
WHERE l.available = TRUE
GROUP BY l.id, l.location_text, l.price, l.available
ORDER BY l.id;

-- Listings NO disponibles (pueden tener 0 fotos)
SELECT 
    l.id,
    l.location_text,
    l.price,
    l.available,
    COUNT(lp.id) as num_fotos
FROM listing l
LEFT JOIN listing_photo lp ON lp.listing_id = l.id
WHERE l.available = FALSE
GROUP BY l.id, l.location_text, l.price, l.available
ORDER BY l.id;

-- ⚠️ INTEGRIDAD: Listings available=TRUE sin fotos (NO DEBE HABER NINGUNO)
SELECT 
    l.id,
    l.location_text,
    l.available,
    COUNT(lp.id) as num_fotos
FROM listing l
LEFT JOIN listing_photo lp ON lp.listing_id = l.id
WHERE l.available = TRUE
GROUP BY l.id, l.location_text, l.available
HAVING COUNT(lp.id) = 0;
-- Si retorna filas: ❌ TRIGGER FALLÓ
-- Si retorna 0 filas: ✅ TRIGGER FUNCIONA

-- ⚠️ INTEGRIDAD: Listings available=TRUE con >5 fotos (NO DEBE HABER NINGUNO)
SELECT 
    l.id,
    l.location_text,
    l.available,
    COUNT(lp.id) as num_fotos
FROM listing l
LEFT JOIN listing_photo lp ON lp.listing_id = l.id
WHERE l.available = TRUE
GROUP BY l.id, l.location_text, l.available
HAVING COUNT(lp.id) > 5;
-- Si retorna filas: ❌ TRIGGER FALLÓ
-- Si retorna 0 filas: ✅ TRIGGER FUNCIONA

-- ⚠️ INTEGRIDAD: Listings con valores negativos (NO DEBE HABER NINGUNO)
SELECT 
    id,
    location_text,
    price,
    rooms,
    bathrooms,
    shared_with_people
FROM listing
WHERE price < 0 OR rooms < 0 OR bathrooms < 0 OR shared_with_people < 0;
-- Si retorna filas: ❌ CHECK CONSTRAINTS FALLARON
-- Si retorna 0 filas: ✅ CHECK CONSTRAINTS FUNCIONAN

-- ============================================================================
-- 4. 📷 FOTOS DE LISTINGS
-- ============================================================================

-- Ver todas las fotos con su listing
SELECT 
    lp.id,
    lp.listing_id,
    l.location_text,
    lp.url,
    lp.mime_type,
    lp.size_bytes,
    lp.sort_order,
    lp.created_at
FROM listing_photo lp
INNER JOIN listing l ON lp.listing_id = l.id
ORDER BY lp.listing_id, lp.sort_order;

-- Contar fotos por listing
SELECT 
    l.id as listing_id,
    l.location_text,
    l.available,
    COUNT(lp.id) as num_fotos
FROM listing l
LEFT JOIN listing_photo lp ON lp.listing_id = l.id
GROUP BY l.id, l.location_text, l.available
ORDER BY l.id;

-- ============================================================================
-- 5. ⭐ FAVORITOS
-- ============================================================================

-- Ver todos los favoritos
SELECT 
    f.id,
    u.username as student_username,
    l.location_text,
    l.price,
    l.available,
    f.created_at as fecha_favorito
FROM favorite f
INNER JOIN users_student s ON f.student_id = s.id
INNER JOIN users_user u ON s.user_id = u.id
INNER JOIN listing l ON f.listing_id = l.id
ORDER BY f.created_at DESC;

-- Favoritos por estudiante
SELECT 
    u.username as student,
    COUNT(f.id) as num_favoritos,
    GROUP_CONCAT(l.location_text SEPARATOR ' | ') as listings_favoritos
FROM users_student s
INNER JOIN users_user u ON s.user_id = u.id
LEFT JOIN favorite f ON f.student_id = s.id
LEFT JOIN listing l ON f.listing_id = l.id
GROUP BY u.username
ORDER BY num_favoritos DESC;

-- Listings más favoritos
SELECT 
    l.id,
    l.location_text,
    l.price,
    l.available,
    COUNT(f.id) as num_favoritos
FROM listing l
LEFT JOIN favorite f ON f.listing_id = l.id
GROUP BY l.id, l.location_text, l.price, l.available
ORDER BY num_favoritos DESC, l.id;

-- Verificar favoritos de un estudiante específico
-- SELECT 
--     f.id,
--     l.location_text,
--     l.price,
--     l.available
-- FROM favorite f
-- INNER JOIN listing l ON f.listing_id = l.id
-- WHERE f.student_id = [STUDENT_ID];

-- ============================================================================
-- 6. 💬 COMENTARIOS (incluyendo anidados)
-- ============================================================================

-- Ver todos los comentarios con estructura de árbol
SELECT 
    c.id,
    c.listing_id,
    l.location_text,
    u.username as author,
    c.parent_comment_id,
    LEFT(c.text, 50) as texto_preview,
    c.created_at
FROM comment c
INNER JOIN users_user u ON c.author_id = u.id
INNER JOIN listing l ON c.listing_id = l.id
ORDER BY c.listing_id, c.id;

-- Comentarios raíz (sin parent)
SELECT 
    c.id,
    c.listing_id,
    l.location_text,
    u.username as author,
    c.text,
    c.created_at
FROM comment c
INNER JOIN users_user u ON c.author_id = u.id
INNER JOIN listing l ON c.listing_id = l.id
WHERE c.parent_comment_id IS NULL
ORDER BY c.listing_id, c.created_at;

-- Comentarios anidados (con parent)
SELECT 
    c.id,
    c.listing_id,
    l.location_text,
    u.username as author,
    c.parent_comment_id,
    parent_u.username as parent_author,
    c.text,
    c.created_at
FROM comment c
INNER JOIN users_user u ON c.author_id = u.id
INNER JOIN listing l ON c.listing_id = l.id
INNER JOIN comment parent_c ON c.parent_comment_id = parent_c.id
INNER JOIN users_user parent_u ON parent_c.author_id = parent_u.id
WHERE c.parent_comment_id IS NOT NULL
ORDER BY c.listing_id, c.parent_comment_id, c.created_at;

-- 🌳 Árbol completo de comentarios con niveles (recursivo)
WITH RECURSIVE comment_tree AS (
    -- Nivel 0: comentarios raíz
    SELECT 
        c.id,
        c.listing_id,
        c.author_id,
        c.parent_comment_id,
        c.text,
        0 as nivel,
        CAST(c.id AS CHAR(200)) as path
    FROM comment c
    WHERE c.parent_comment_id IS NULL
    
    UNION ALL
    
    -- Niveles siguientes: respuestas
    SELECT 
        c.id,
        c.listing_id,
        c.author_id,
        c.parent_comment_id,
        c.text,
        ct.nivel + 1,
        CONCAT(ct.path, ' > ', c.id)
    FROM comment c
    INNER JOIN comment_tree ct ON c.parent_comment_id = ct.id
)
SELECT 
    ct.id,
    ct.listing_id,
    l.location_text,
    u.username,
    ct.parent_comment_id,
    ct.nivel,
    CONCAT(REPEAT('  ', ct.nivel), '└─ ') as indent,
    LEFT(ct.text, 50) as text_preview,
    ct.path
FROM comment_tree ct
INNER JOIN users_user u ON ct.author_id = u.id
INNER JOIN listing l ON ct.listing_id = l.id
ORDER BY ct.listing_id, ct.path;

-- ⚠️ INTEGRIDAD: Comentarios con parent en diferente listing (NO DEBE HABER NINGUNO)
SELECT 
    c.id as comment_id,
    c.listing_id as comment_listing,
    c.parent_comment_id,
    parent_c.listing_id as parent_listing,
    'VIOLACIÓN' as status
FROM comment c
INNER JOIN comment parent_c ON c.parent_comment_id = parent_c.id
WHERE c.listing_id != parent_c.listing_id;
-- Si retorna filas: ❌ TRIGGER FALLÓ
-- Si retorna 0 filas: ✅ TRIGGER FUNCIONA

-- ============================================================================
-- 7. ⭐ REVIEWS
-- ============================================================================

-- Ver todas las reviews con información completa
SELECT 
    r.id,
    r.listing_id,
    l.location_text,
    s.id as student_id,
    u.username as student_username,
    r.rating,
    r.text,
    r.created_at
FROM review r
INNER JOIN users_student s ON r.student_id = s.id
INNER JOIN users_user u ON s.user_id = u.id
INNER JOIN listing l ON r.listing_id = l.id
ORDER BY r.listing_id, r.created_at;

-- Popularity calculado por listing (promedio de reviews)
SELECT 
    l.id as listing_id,
    l.location_text,
    l.popularity as popularity_actual,
    COALESCE(AVG(r.rating), 0) as popularity_calculado,
    COUNT(r.id) as num_reviews
FROM listing l
LEFT JOIN review r ON r.listing_id = l.id
GROUP BY l.id, l.location_text, l.popularity
ORDER BY l.id;

-- ⚠️ INTEGRIDAD: Reviews duplicados (mismo estudiante, mismo listing - NO DEBE HABER)
SELECT 
    r.student_id,
    r.listing_id,
    u.username,
    l.location_text,
    COUNT(*) as num_reviews_duplicados
FROM review r
INNER JOIN users_student s ON r.student_id = s.id
INNER JOIN users_user u ON s.user_id = u.id
INNER JOIN listing l ON r.listing_id = l.id
GROUP BY r.student_id, r.listing_id, u.username, l.location_text
HAVING COUNT(*) > 1;
-- Si retorna filas: ❌ UNIQUE CONSTRAINT FALLÓ
-- Si retorna 0 filas: ✅ UNIQUE CONSTRAINT FUNCIONA

-- ============================================================================
-- 8. 🚨 DENUNCIAS (Reports)
-- ============================================================================

-- Ver todas las denuncias
SELECT 
    r.id,
    r.reporter_id,
    u_reporter.username as reporter_username,
    r.reason,
    r.status,
    r.created_at,
    CASE 
        WHEN ur.report_id IS NOT NULL THEN 'USER_REPORT'
        WHEN lr.report_id IS NOT NULL THEN 'LISTING_REPORT'
        ELSE 'UNKNOWN'
    END as tipo_reporte
FROM report r
INNER JOIN users_user u_reporter ON r.reporter_id = u_reporter.id
LEFT JOIN user_report ur ON ur.report_id = r.id
LEFT JOIN listing_report lr ON lr.report_id = r.id
ORDER BY r.created_at DESC;

-- Denuncias de USUARIOS
SELECT 
    r.id as report_id,
    u_reporter.username as reporter,
    u_reported.username as reported_user,
    r.reason,
    r.status,
    r.created_at
FROM report r
INNER JOIN user_report ur ON ur.report_id = r.id
INNER JOIN users_user u_reporter ON r.reporter_id = u_reporter.id
INNER JOIN users_user u_reported ON ur.reported_user_id = u_reported.id
ORDER BY r.created_at DESC;

-- Denuncias de LISTINGS
SELECT 
    r.id as report_id,
    u_reporter.username as reporter,
    l.location_text as reported_listing,
    r.reason,
    r.status,
    r.created_at
FROM report r
INNER JOIN listing_report lr ON lr.report_id = r.id
INNER JOIN users_user u_reporter ON r.reporter_id = u_reporter.id
INNER JOIN listing l ON lr.listing_id = l.id
ORDER BY r.created_at DESC;

-- ⚠️ INTEGRIDAD: Reports sin UserReport ni ListingReport (VIOLACIÓN XOR - NO DEBE HABER)
SELECT 
    r.id,
    r.reporter_id,
    u.username,
    'NO_XOR_VIOLATION' as status
FROM report r
INNER JOIN users_user u ON r.reporter_id = u.id
LEFT JOIN user_report ur ON ur.report_id = r.id
LEFT JOIN listing_report lr ON lr.report_id = r.id
WHERE (ur.report_id IS NULL AND lr.report_id IS NULL) OR (ur.report_id IS NOT NULL AND lr.report_id IS NOT NULL);
-- Si retorna filas: ❌ TRIGGERS XOR FALLARON
-- Si retorna 0 filas: ✅ TRIGGERS XOR FUNCIONAN

-- Usuarios suspendidos (suspension_end_at futuro)
SELECT 
    u.id,
    u.username,
    u.email,
    u.suspension_end_at,
    DATEDIFF(u.suspension_end_at, CURDATE()) as dias_restantes
FROM users_user u
WHERE u.suspension_end_at > CURDATE()
ORDER BY u.suspension_end_at;

-- ============================================================================
-- 9. 📊 ESTADÍSTICAS GENERALES
-- ============================================================================

-- Resumen general del sistema
SELECT 
    'Usuarios totales' as metrica,
    COUNT(*) as valor
FROM users_user
UNION ALL
SELECT 'Estudiantes', COUNT(*) FROM users_student
UNION ALL
SELECT 'Arrendadores', COUNT(*) FROM users_landlord
UNION ALL
SELECT 'Admins', COUNT(*) FROM admin
UNION ALL
SELECT 'Zonas', COUNT(*) FROM zone
UNION ALL
SELECT 'Listings totales', COUNT(*) FROM listing
UNION ALL
SELECT 'Listings disponibles', COUNT(*) FROM listing WHERE available = TRUE
UNION ALL
SELECT 'Fotos totales', COUNT(*) FROM listing_photo
UNION ALL
SELECT 'Favoritos totales', COUNT(*) FROM favorite
UNION ALL
SELECT 'Comentarios totales', COUNT(*) FROM comment
UNION ALL
SELECT 'Comentarios raíz', COUNT(*) FROM comment WHERE parent_comment_id IS NULL
UNION ALL
SELECT 'Comentarios anidados', COUNT(*) FROM comment WHERE parent_comment_id IS NOT NULL
UNION ALL
SELECT 'Reviews totales', COUNT(*) FROM review
UNION ALL
SELECT 'Denuncias totales', COUNT(*) FROM report
UNION ALL
SELECT 'Denuncias de usuarios', COUNT(*) FROM user_report
UNION ALL
SELECT 'Denuncias de listings', COUNT(*) FROM listing_report
UNION ALL
SELECT 'Usuarios suspendidos', COUNT(*) FROM users_user WHERE suspension_end_at > CURDATE();

-- Top 5 listings más populares
SELECT 
    l.id,
    l.location_text,
    l.price,
    l.popularity,
    l.views,
    COUNT(r.id) as num_reviews,
    z.name as zona
FROM listing l
INNER JOIN zone z ON l.zone_id = z.id
LEFT JOIN review r ON r.listing_id = l.id
GROUP BY l.id, l.location_text, l.price, l.popularity, l.views, z.name
ORDER BY l.popularity DESC, l.views DESC
LIMIT 5;

-- ============================================================================
-- 10. 🔧 VERIFICACIÓN DE TRIGGERS
-- ============================================================================

-- Ver todos los triggers activos
SHOW TRIGGERS FROM umigo;

-- Contar triggers por tabla
SELECT 
    EVENT_OBJECT_TABLE as tabla,
    COUNT(*) as num_triggers
FROM information_schema.TRIGGERS 
WHERE TRIGGER_SCHEMA = 'umigo'
GROUP BY EVENT_OBJECT_TABLE
ORDER BY num_triggers DESC;

-- ============================================================================
-- 11. 🧪 QUERIES PARA PROBAR FUNCIONALIDADES
-- ============================================================================

-- PROBAR: Intentar crear listing con precio negativo (debe fallar)
-- INSERT INTO listing (owner_id, price, location_text, lat, lng, zone_id, rooms, bathrooms, shared_with_people, utilities_price, available, created_at, updated_at)
-- VALUES (1, -100000, 'Test precio negativo', 4.62, -74.06, 1, 2, 1, 0, 50000, FALSE, NOW(), NOW());
-- Esperado: ERROR 3819 (HY000): Check constraint 'listing_chk_1' is violated.

-- PROBAR: Intentar poner available=TRUE sin fotos (debe fallar)
-- UPDATE listing SET available = TRUE WHERE id = [LISTING_SIN_FOTOS];
-- Esperado: ERROR 1644 (45000): Listing debe tener al menos 1 foto para estar disponible

-- PROBAR: Intentar crear comentario con parent en diferente listing (debe fallar)
-- INSERT INTO comment (listing_id, author_id, text, parent_comment_id, created_at, updated_at)
-- VALUES ([LISTING_2_ID], [USER_ID], 'Test parent incorrecto', [COMMENT_DE_LISTING_1_ID], NOW(), NOW());
-- Esperado: ERROR 1644 (45000): Reply must belong to same listing as parent comment

-- ============================================================================
-- FIN DE QUERIES DE VERIFICACIÓN
-- ============================================================================
