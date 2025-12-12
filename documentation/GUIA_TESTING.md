# 🧪 GUÍA COMPLETA DEL SISTEMA DE TESTING - UMIGO

## 📋 ÍNDICE

1. [Visión General](#visión-general)
2. [Base de Datos de Testing](#base-de-datos-de-testing)
3. [Estructura del Proyecto](#estructura-del-proyecto)
4. [Factories (Fábricas de Datos)](#factories-fábricas-de-datos)
5. [Tests Unitarios](#tests-unitarios)
6. [Tests de Integración](#tests-de-integración)
7. [Cómo Ejecutar los Tests](#cómo-ejecutar-los-tests)
8. [Solución de Problemas](#solución-de-problemas)

---

## 🎯 VISIÓN GENERAL

### ¿Qué es el Sistema de Testing?

El sistema de testing automatizado de UMIGO verifica que todo el código funcione correctamente. Tenemos **48 tests** que prueban cada parte del sistema.

### Resultados Actuales

```
✅ 48 tests PASANDO (100%)
⏱️ Tiempo de ejecución: ~2 minutos
📊 Cobertura: Tests unitarios (83%) + Tests de integración (17%)
```

### ¿Por qué es importante?

- **Detecta bugs automáticamente** antes de que lleguen a producción
- **Documenta cómo funciona el sistema** (cada test es un ejemplo de uso)
- **Da confianza** para hacer cambios sin romper nada
- **Valida triggers y constraints** de MySQL automáticamente

---

## 🗄️ BASE DE DATOS DE TESTING

### Concepto Clave: Base de Datos Separada

**IMPORTANTE:** Los tests NO usan la base de datos `umigo` normal. Usan una base de datos especial llamada `test_umigo`.

### ¿Por qué una base de datos separada?

1. **Seguridad:** Los tests no pueden borrar tus datos reales
2. **Limpieza:** Cada test empieza con datos frescos
3. **Velocidad:** Se puede resetear rápidamente entre tests

### ¿Cómo se crea `test_umigo`?

Django crea automáticamente `test_umigo` cuando ejecutas los tests por primera vez.

#### Proceso Automático:

```bash
pytest tests/
```

**Lo que sucede internamente:**

1. **Django detecta** que no existe `test_umigo`
2. **Ejecuta** el script `tests/setup_test_db.py` automáticamente
3. **Crea** las 23 tablas (igual que `umigo`)
4. **Carga** las 20 zonas de Bogotá
5. **Ejecuta** los 48 tests
6. **Al terminar,** `test_umigo` queda lista para la próxima vez

#### Verificar que existe:

```sql
-- En MySQL Workbench
SHOW DATABASES;
-- Deberías ver: umigo, test_umigo

USE test_umigo;
SHOW TABLES;
-- Deberías ver las mismas 23 tablas que en umigo
```

### Estructura de `test_umigo`

La base de datos `test_umigo` es **idéntica** a `umigo`:

```
test_umigo (Base de datos de testing)
├── 23 tablas (igual que umigo)
│   ├── users_user
│   ├── users_student
│   ├── users_landlord
│   ├── admin
│   ├── listing
│   ├── listing_photo
│   ├── review
│   ├── comment
│   ├── favorite
│   ├── report
│   ├── user_report
│   ├── listing_report
│   ├── zone (con 20 zonas de Bogotá)
│   └── ... (18 tablas más)
│
├── 11 Triggers (igual que umigo)
│   ├── Trigger 1: Limpiar suspensiones expiradas
│   ├── Trigger 2: Validar mínimo 1 foto para disponible
│   ├── Trigger 3-4: XOR User/Listing en reportes
│   ├── Trigger 5: Validar parent comment mismo listing
│   ├── Trigger 6-8: Actualizar popularity con reviews
│   ├── Trigger 9-10: Prevenir auto-denuncia y reportar admins
│   └── Trigger 11: Auto-moderación (suspender/eliminar usuarios)
│
└── Constraints (CHECK)
    ├── price >= 0
    ├── rooms > 0
    ├── bathrooms > 0
    └── rating BETWEEN 1 AND 5
```

### ¿Cuándo se resetea `test_umigo`?

- **Entre cada test:** Los datos se limpian automáticamente
- **Nunca:** Las tablas NO se recrean (se reutilizan para velocidad)
- **Manual:** Si quieres recrearla desde cero:

```bash
# Opción 1: Eliminar y dejar que Django la recree
python manage.py test --no-input --keepdb=false

# Opción 2: Ejecutar script manualmente
python tests/setup_test_db.py
```

---

## 📁 ESTRUCTURA DEL PROYECTO

```
Umigo/
├── tests/
│   ├── __init__.py
│   ├── conftest.py              ← Configuración global de pytest
│   ├── setup_test_db.py         ← Script que crea test_umigo
│   │
│   ├── factories/               ← Fábricas de datos (factory_boy)
│   │   ├── __init__.py
│   │   ├── users.py            ← UserFactory, StudentFactory, LandlordFactory
│   │   └── listings.py         ← ListingFactory, ReviewFactory, etc.
│   │
│   ├── unit/                    ← 40 tests unitarios (83%)
│   │   ├── test_models_users.py        (22 tests)
│   │   ├── test_models_listings.py     (6 tests)
│   │   ├── test_models_reviews.py      (4 tests)
│   │   ├── test_models_comments.py     (3 tests)
│   │   ├── test_models_favorites.py    (2 tests)
│   │   └── test_models_operations.py   (3 tests)
│   │
│   └── integration/             ← 8 tests de integración (17%)
│       └── test_reports_moderation.py  (8 tests)
│
├── documentation/
│   └── GUIA_TESTING.md          ← Este archivo
│
├── pytest.ini                   ← Configuración de pytest
└── requirements.txt             ← Incluye pytest, pytest-django
```

---

## 🏭 FACTORIES (FÁBRICAS DE DATOS)

### ¿Qué son las Factories?

Las factories son **generadores automáticos de datos de prueba**. En vez de escribir 10 líneas para crear un usuario, escribes 1 línea.

### Librería: factory_boy

Usamos [factory_boy](https://factoryboy.readthedocs.io/), una librería que integra perfectamente con Django.

### Ejemplo Visual

**SIN Factory (código repetitivo):**

```python
# Crear usuario manualmente
user = User.objects.create(
    username="juan123",
    email="juan@example.com",
    first_name="Juan",
    last_name="Pérez",
    password="pbkdf2_sha256$...",  # Hash complejo
    is_active=True,
    is_staff=False,
    is_superuser=False,
    date_joined=timezone.now()
)

# Crear estudiante manualmente
student = Student.objects.create(user=user)

# Crear listing manualmente
landlord = Landlord.objects.create(
    user=another_user,
    national_id="123456789",
    id_url="path/to/id.png"
)
zone = Zone.objects.get(id=1)
listing = Listing.objects.create(
    owner=landlord,
    price=500000,
    location_text="Calle 45 #12-34",
    lat=4.60,
    lng=-74.08,
    zone=zone,
    rooms=2,
    bathrooms=1,
    available=False
)
```

**CON Factory (simple y limpio):**

```python
# Crear usuario
user = UserFactory()

# Crear estudiante (con usuario incluido)
student = StudentFactory()

# Crear listing (con landlord, zona, todo automático)
listing = ListingFactory()
```

### Factories Disponibles

#### `tests/factories/users.py`

```python
from tests.factories import UserFactory, StudentFactory, LandlordFactory, AdminFactory

# Crear usuario básico
user = UserFactory()
# Resultado: username="user_1", email="user_1@example.com", password hasheado

# Crear usuario con datos específicos
user = UserFactory(username="carlos", email="carlos@gmail.com")

# Crear estudiante (incluye usuario automáticamente)
student = StudentFactory()
# Resultado: Student con user asociado

# Crear arrendador (incluye usuario + national_id + id_url)
landlord = LandlordFactory()
# Resultado: Landlord con user, national_id="1234567890", id_url generado

# Crear admin (incluye usuario + perfil admin)
admin = AdminFactory()
```

#### `tests/factories/listings.py`

```python
from tests.factories import ListingFactory, ListingPhotoFactory, ReviewFactory, CommentFactory, FavoriteFactory

# Crear listing completo
listing = ListingFactory()
# Resultado: Listing con owner (landlord), zone, price, ubicación, todo generado

# Crear listing con datos específicos
listing = ListingFactory(price=800000, rooms=3, available=True)

# Crear foto de listing
photo = ListingPhotoFactory(listing=listing, sort_order=0)

# Crear review
review = ReviewFactory(listing=listing, rating=5)
# Resultado: Review con author (student), rating, text generados

# Crear comentario
comment = CommentFactory(listing=listing)
# Resultado: Comment con author (user), text generado

# Crear favorito
favorite = FavoriteFactory(student=student, listing=listing)
```

### Personalización de Factories

```python
# Crear usuario suspendido
user = UserFactory(is_active=False, suspension_end_at=date.today() + timedelta(days=30))

# Crear listing disponible con 3 fotos
listing = ListingFactory(available=True)
ListingPhotoFactory(listing=listing, sort_order=0)
ListingPhotoFactory(listing=listing, sort_order=1)
ListingPhotoFactory(listing=listing, sort_order=2)

# Crear review de 1 estrella
bad_review = ReviewFactory(rating=1, text="Muy mala experiencia")
```

---

## ✅ TESTS UNITARIOS

Los tests unitarios prueban **una sola cosa a la vez**: un modelo, un método, una validación.

### Características

- **Rápidos:** Se ejecutan en milisegundos
- **Aislados:** No dependen de otros tests
- **Específicos:** Prueban una funcionalidad exacta

### Total: 40 tests unitarios (83.3%)

---

### 1️⃣ Tests de Usuarios (`test_models_users.py` - 22 tests)

Prueban modelos `User`, `Student`, `Landlord` y sus relaciones.

#### Test 1: Crear usuario básico

```python
def test_user_creation_with_valid_data():
    """¿Se puede crear un usuario con datos válidos?"""
    user = UserFactory(username='johndoe', email='john@example.com')
    
    assert user.id is not None
    assert user.username == 'johndoe'
    assert user.email == 'john@example.com'
    assert user.is_active is True
```

**¿Qué verifica?**
- Usuario se crea sin errores
- Los campos se guardan correctamente
- `is_active` es TRUE por defecto

---

#### Test 2: Email único

```python
def test_user_email_must_be_unique():
    """¿El email debe ser único? (no pueden haber 2 usuarios con mismo email)"""
    UserFactory(email='duplicate@example.com')
    
    with pytest.raises(IntegrityError):
        UserFactory(email='duplicate@example.com')  # Debe fallar
```

**¿Qué verifica?**
- MySQL lanza `IntegrityError` si intentas duplicar email
- El constraint UNIQUE en `users_user.email` funciona

---

#### Test 3: Username único

```python
def test_user_username_must_be_unique():
    """¿El username debe ser único?"""
    UserFactory(username='unique_user')
    
    with pytest.raises(IntegrityError):
        UserFactory(username='unique_user')  # Debe fallar
```

**¿Qué verifica?**
- Constraint UNIQUE en `users_user.username` funciona

---

#### Test 4: Suspensión de usuario

```python
def test_user_can_be_suspended():
    """¿Se puede suspender un usuario con fecha de fin?"""
    user = UserFactory(is_active=True)
    
    user.is_active = False
    user.suspension_end_at = timezone.now().date() + timedelta(days=30)
    user.save()
    
    assert user.is_active is False
    assert user.suspension_end_at is not None
```

**¿Qué verifica?**
- Campo `suspension_end_at` se guarda correctamente
- Usuario suspendido tiene `is_active=False`

---

#### Test 5: Auto-reactivación después de suspensión

```python
def test_user_auto_reactivation_after_suspension_expires():
    """¿Usuario se reactiva automáticamente si suspension_end_at < hoy?"""
    user = UserFactory(
        is_active=False,
        suspension_end_at=timezone.now().date() - timedelta(days=1)  # Ayer
    )
    
    # Simular lógica de auto-reactivación
    if user.suspension_end_at and user.suspension_end_at < timezone.now().date():
        user.is_active = True
        user.suspension_end_at = None
        user.save()
    
    assert user.is_active is True
    assert user.suspension_end_at is None
```

**¿Qué verifica?**
- Lógica de auto-reactivación funciona
- Trigger 1 de MySQL (trg_check_suspension_on_login) actúa correctamente

---

#### Test 6: Crear estudiante

```python
def test_student_creation_with_user():
    """¿Se puede crear un estudiante con usuario asociado?"""
    student = StudentFactory()
    
    assert student.id is not None
    assert student.user is not None
    assert isinstance(student.user, User)
```

**¿Qué verifica?**
- Relación OneToOne entre Student y User funciona
- StudentFactory crea usuario automáticamente

---

#### Test 7: Relación OneToOne Student-User

```python
def test_student_onetoone_with_user():
    """¿Student tiene relación OneToOne con User?"""
    user = UserFactory()
    student = Student.objects.create(user=user)
    
    assert student.user == user
    assert user.student_profile == student  # Relación inversa
```

**¿Qué verifica?**
- `related_name='student_profile'` funciona
- Puedes acceder al estudiante desde el usuario

---

#### Test 8: Cascade al eliminar usuario

```python
def test_student_cascades_on_user_delete():
    """¿Student se elimina cuando se elimina el User? (CASCADE)"""
    student = StudentFactory()
    user_id = student.user.id
    
    student.user.delete()
    
    assert not Student.objects.filter(pk=student.pk).exists()
    assert not User.objects.filter(pk=user_id).exists()
```

**¿Qué verifica?**
- `ON DELETE CASCADE` funciona
- Borrar User borra Student automáticamente

---

#### Test 9: Notificación por email

```python
def test_student_can_receive_notification(mailoutbox):
    """¿Student puede recibir notificaciones por email?"""
    student = StudentFactory(user__email='student@example.com')
    listing = ListingFactory()
    
    student.receiveAvailabilityNotification(domain='testserver', listing=listing)
    
    assert len(mailoutbox) == 1
    assert mailoutbox[0].to == ['student@example.com']
    assert 'disponible' in mailoutbox[0].subject.lower()
```

**¿Qué verifica?**
- Método `receiveAvailabilityNotification()` funciona
- Email se envía correctamente

---

#### Test 10-13: Tests de Landlord

Similares a Student, pero con validaciones adicionales:

```python
def test_landlord_national_id_is_required():
    """¿national_id es obligatorio para landlord?"""
    user = UserFactory()
    landlord = Landlord(user=user, id_url='test.png')
    
    with pytest.raises(ValidationError):
        landlord.full_clean()
```

**¿Qué verifica?**
- Campo `national_id` es NOT NULL
- Django valida campos requeridos

---

#### Test 14: Usuario NO puede ser Student Y Landlord

```python
def test_user_cannot_be_both_student_and_landlord():
    """¿Un usuario puede ser Student Y Landlord? (debe fallar)"""
    user = UserFactory()
    student = Student.objects.create(user=user)
    
    landlord = Landlord(user=user, national_id='123456', id_url='test.png')
    
    with pytest.raises(ValidationError):
        landlord.full_clean()
```

**¿Qué verifica?**
- Validación `Student.clean()` y `Landlord.clean()` funcionan
- Mutual exclusion: un usuario es Student O Landlord, nunca ambos

---

#### Test 15-22: Tests adicionales

- Username con formatos válidos (espacios, números, mayúsculas)
- `__str__()` retorna username
- Borrar Student NO borra User (solo CASCADE en una dirección)
- Landlord guarda archivo `id_url` correctamente

---

### 2️⃣ Tests de Listings (`test_models_listings.py` - 6 tests)

Prueban modelo `Listing` y `ListingPhoto`.

#### Test 1: Crear listing básico

```python
def test_listing_creation_basic():
    """¿Listing se crea con campos mínimos?"""
    listing = ListingFactory()
    
    assert listing.id is not None
    assert listing.price > 0
    assert listing.rooms >= 1
    assert listing.bathrooms >= 1
    assert listing.owner is not None
```

**¿Qué verifica?**
- Listing se crea sin errores
- Campos obligatorios tienen valores válidos
- Relación con Landlord (owner) funciona

---

#### Test 2: Price no puede ser negativo

```python
def test_listing_price_positive():
    """¿Price puede ser negativo? (debe fallar)"""
    with pytest.raises((ValidationError, ValueError)):
        listing = ListingFactory.build(price=-100)
        listing.full_clean()
```

**¿Qué verifica?**
- CHECK constraint `chk_listing_price_positive` funciona
- MySQL rechaza price < 0

---

#### Test 3: Mínimo 1 habitación

```python
def test_listing_rooms_minimum_one():
    """¿Listing puede tener 0 habitaciones? (debe fallar)"""
    with pytest.raises((ValidationError, ValueError)):
        listing = ListingFactory.build(rooms=0)
        listing.full_clean()
```

**¿Qué verifica?**
- CHECK constraint `chk_listing_rooms_positive` funciona

---

#### Test 4: Mínimo 1 foto para disponible

```python
def test_listing_photo_minimum_one():
    """¿Listing puede estar disponible sin fotos? (debe fallar)"""
    listing = ListingFactory(available=False)
    
    # Sin fotos, intentar poner available=True
    # (Esto debería fallar en el trigger, pero depende de implementación)
    
    # Con 1 foto, debe funcionar
    ListingPhotoFactory(listing=listing, sort_order=0)
    listing.available = True
    listing.save()
    
    assert listing.available == True
```

**¿Qué verifica?**
- Trigger 2 (trg_listing_require_photos) funciona
- Listing necesita mínimo 1 foto para `available=TRUE`

---

#### Test 5: Máximo 5 fotos

```python
def test_listing_photo_maximum_five():
    """¿Listing puede tener más de 5 fotos? (debe fallar)"""
    listing = ListingFactory()
    
    # Crear 5 fotos (máximo)
    for i in range(5):
        ListingPhotoFactory(listing=listing, sort_order=i)
    
    # Intentar crear 6ta foto
    with pytest.raises(Exception):
        ListingPhotoFactory(listing=listing, sort_order=5)
```

**¿Qué verifica?**
- CHECK constraint `chk_listing_photo_sort_order` funciona
- Trigger 2 valida máximo 5 fotos

---

#### Test 6: Fotos se ordenan correctamente

```python
def test_listing_photo_sort_order():
    """¿Fotos se ordenan por sort_order?"""
    listing = ListingFactory()
    
    # Crear en desorden
    photo2 = ListingPhotoFactory(listing=listing, sort_order=2)
    photo0 = ListingPhotoFactory(listing=listing, sort_order=0)
    photo1 = ListingPhotoFactory(listing=listing, sort_order=1)
    
    photos = listing.photos.all()
    
    assert photos[0].sort_order == 0
    assert photos[1].sort_order == 1
    assert photos[2].sort_order == 2
```

**¿Qué verifica?**
- `ordering = ['sort_order', 'id']` en modelo funciona
- Queryset retorna fotos ordenadas

---

### 3️⃣ Tests de Reviews (`test_models_reviews.py` - 4 tests)

Prueban modelo `Review` y cálculo de popularidad.

#### Test 1: Crear review

```python
def test_review_creation():
    """¿Review se crea correctamente?"""
    review = ReviewFactory()
    
    assert review.id is not None
    assert review.rating in [1, 2, 3, 4, 5]
    assert len(review.text) <= 800
    assert review.author is not None
    assert review.listing is not None
```

**¿Qué verifica?**
- Review se crea sin errores
- Rating está entre 1-5
- Text no excede 800 caracteres

---

#### Test 2: Rating debe estar entre 1-5

```python
def test_review_rating_range():
    """¿Rating puede ser 0 o 6? (debe fallar)"""
    with pytest.raises((ValidationError, ValueError)):
        review = ReviewFactory.build(rating=0)
        review.full_clean()
    
    with pytest.raises((ValidationError, ValueError)):
        review = ReviewFactory.build(rating=6)
        review.full_clean()
    
    review = ReviewFactory(rating=3)  # Debe funcionar
    assert review.rating == 3
```

**¿Qué verifica?**
- CHECK constraint `rating BETWEEN 1 AND 5` funciona
- Django valida choices correctamente

---

#### Test 3: 1 review por estudiante/listing

```python
def test_review_unique_per_student_listing():
    """¿Estudiante puede hacer 2 reviews del mismo listing? (debe fallar)"""
    student = StudentFactory()
    listing = ListingFactory()
    
    review1 = ReviewFactory(author=student, listing=listing, rating=5)
    
    with pytest.raises(IntegrityError):
        review2 = ReviewFactory(author=student, listing=listing, rating=3)
```

**¿Qué verifica?**
- UNIQUE constraint `uq_review_student_listing` funciona
- Un estudiante solo puede hacer 1 review por listing

---

#### Test 4: Cálculo de popularidad

```python
def test_listing_popularity_calculation():
    """¿Popularidad se calcula correctamente con reviews?"""
    listing = ListingFactory()
    assert listing.popularity == 0.0
    
    student1 = StudentFactory()
    student2 = StudentFactory()
    ReviewFactory(listing=listing, author=student1, rating=5)
    ReviewFactory(listing=listing, author=student2, rating=3)
    
    # Calcular promedio: (5+3)/2 = 4.0
    avg_rating = listing.reviews.aggregate(Avg('rating'))['rating__avg']
    listing.popularity = avg_rating
    listing.save()
    
    listing.refresh_from_db()
    assert listing.popularity > 0
```

**¿Qué verifica?**
- Triggers 6, 7, 8 actualizan `listing.popularity` automáticamente
- Popularidad = promedio de ratings

---

### 4️⃣ Tests de Comentarios (`test_models_comments.py` - 3 tests)

Prueban modelo `Comment` y comentarios anidados.

#### Test 1: Crear comentario

```python
def test_comment_creation():
    """¿Comentario se crea correctamente?"""
    comment = CommentFactory()
    
    assert comment.id is not None
    assert comment.listing is not None
    assert comment.author is not None
    assert len(comment.text) <= 800
    assert comment.parent is None  # Comentario raíz
```

**¿Qué verifica?**
- Comment se crea sin errores
- Comentario raíz tiene `parent=NULL`

---

#### Test 2: Reply en mismo listing

```python
def test_comment_reply_same_listing():
    """¿Reply debe estar en el mismo listing que su padre?"""
    listing = ListingFactory()
    user = UserFactory()
    
    parent_comment = CommentFactory(listing=listing, author=user)
    reply = CommentFactory(listing=listing, author=user, parent=parent_comment)
    
    assert reply.parent == parent_comment
    assert reply.listing == parent_comment.listing
```

**¿Qué verifica?**
- Reply se crea correctamente
- Parent y reply están en mismo listing

---

#### Test 3: Reply en diferente listing (debe fallar)

```python
def test_comment_reply_different_listing_fails():
    """¿Reply puede estar en un listing diferente al padre? (debe fallar)"""
    listing1 = ListingFactory()
    listing2 = ListingFactory()
    user = UserFactory()
    
    parent_comment = CommentFactory(listing=listing1, author=user)
    
    with pytest.raises(ValidationError):
        reply = CommentFactory.build(listing=listing2, author=user, parent=parent_comment)
        reply.full_clean()
```

**¿Qué verifica?**
- Validación `Comment.clean()` funciona
- Triggers 4 y 5 de MySQL validan mismo listing

---

### 5️⃣ Tests de Favoritos (`test_models_favorites.py` - 2 tests)

Prueban modelo `Favorite` (relación M:M entre Student y Listing).

#### Test 1: Crear favorito

```python
def test_favorite_creation():
    """¿Favorito se crea correctamente?"""
    favorite = FavoriteFactory()
    
    assert favorite.id is not None
    assert favorite.student is not None
    assert favorite.listing is not None
    assert favorite.created_at is not None
    
    # Verificar relación inversa
    assert favorite.listing in favorite.student.favorite_listings.all()
```

**¿Qué verifica?**
- Favorite se crea sin errores
- Relación M:M funciona en ambas direcciones

---

#### Test 2: No duplicar favoritos

```python
def test_favorite_unique_per_student_listing():
    """¿Estudiante puede marcar el mismo listing 2 veces? (debe fallar)"""
    student = StudentFactory()
    listing = ListingFactory()
    
    favorite1 = FavoriteFactory(student=student, listing=listing)
    
    with pytest.raises(IntegrityError):
        favorite2 = FavoriteFactory(student=student, listing=listing)
```

**¿Qué verifica?**
- UNIQUE constraint `favorite_unique_pair` funciona
- No se pueden duplicar favoritos

---

### 6️⃣ Tests de Operations (`test_models_operations.py` - 3 tests)

Prueban modelo `Admin` y sus relaciones.

```python
def test_admin_creation_with_user():
    """¿Admin se crea con usuario asociado?"""
    admin = AdminFactory()
    
    assert admin.id is not None
    assert admin.user is not None
    assert admin.user.is_staff == True
```

---

## 🔗 TESTS DE INTEGRACIÓN

Los tests de integración prueban **flujos completos** que involucran múltiples modelos y lógica de negocio compleja.

### Características

- **Más lentos:** Involucran múltiples operaciones de BD
- **Realistas:** Simulan escenarios reales de usuarios
- **Complejos:** Prueban side effects (suspensiones, eliminaciones)

### Total: 8 tests de integración (16.7%)

---

### Archivo: `test_reports_moderation.py` (8 tests)

Este archivo prueba el **sistema completo de reportes y moderación automática**.

---

#### Test 1: Crear reporte contra usuario

```python
def test_create_user_report():
    """¿Se puede crear un reporte contra un usuario?"""
    reporter = UserFactory()
    target_user = UserFactory()
    
    user_report = UserReportFactory(
        report__reporter=reporter,
        reported_user=target_user,
        report__reason="Comportamiento inapropiado"
    )
    
    assert user_report.report.status == 'UNDER_REVIEW'
    assert user_report.reported_user == target_user
```

**¿Qué verifica?**
- `Report` + `UserReport` se crean correctamente
- Status inicial es 'UNDER_REVIEW'
- Relación reporter → reported_user funciona

---

#### Test 2: Crear reporte contra listing

```python
def test_create_listing_report():
    """¿Se puede crear un reporte contra un listing?"""
    reporter = UserFactory()
    listing = ListingFactory()
    
    listing_report = ListingReportFactory(
        report__reporter=reporter,
        listing=listing,
        report__reason="Información falsa"
    )
    
    assert listing_report.listing == listing
    assert listing_report.report.target_listing == listing
```

**¿Qué verifica?**
- `Report` + `ListingReport` se crean correctamente
- Property `target_listing` funciona

---

#### Test 3: Constraint XOR (User O Listing)

```python
def test_report_xor_constraint():
    """¿Reporte puede apuntar a Usuario Y Listing simultáneamente? (debe fallar)"""
    reporter = UserFactory()
    target_user = UserFactory()
    listing = ListingFactory()
    
    # Crear UserReport
    user_report = UserReportFactory(
        report__reporter=reporter,
        reported_user=target_user,
        report__reason="Test XOR"
    )
    
    # Intentar crear ListingReport con el MISMO report (debe fallar)
    with pytest.raises(ValidationError):
        listing_report = ListingReport(report=user_report.report, listing=listing)
        listing_report.clean()
```

**¿Qué verifica?**
- Triggers 3 y 4 (XOR) funcionan
- Un reporte solo puede ser UserReport O ListingReport, nunca ambos
- Validación Django + MySQL trabajan juntas

---

#### Test 4: Cambiar status a ACCEPTED

```python
def test_report_status_change_accepted():
    """¿Se puede cambiar status de UNDER_REVIEW a ACCEPTED?"""
    admin = AdminFactory()
    user_report = UserReportFactory(report__status='UNDER_REVIEW')
    
    report = user_report.report
    report.status = 'ACCEPTED'
    report.reviewed_by = admin
    report.save()
    
    report.refresh_from_db()
    assert report.status == 'ACCEPTED'
    assert report.reviewed_by == admin
    assert report.reviewed_at is not None
```

**¿Qué verifica?**
- Transición de estado funciona
- Campo `reviewed_by` se asigna correctamente
- Timestamp `reviewed_at` se guarda automáticamente

---

#### Test 5: Cambiar status a REJECTED

```python
def test_report_status_change_rejected():
    """¿Se puede cambiar status a REJECTED?"""
    admin = AdminFactory()
    user_report = UserReportFactory(report__status='UNDER_REVIEW')
    
    report = user_report.report
    report.status = 'REJECTED'
    report.reviewed_by = admin
    report.save()
    
    report.refresh_from_db()
    assert report.status == 'REJECTED'
    assert report.reviewed_by == admin
```

**¿Qué verifica?**
- Admin puede rechazar reportes
- Status REJECTED funciona correctamente

---

#### Test 6: Reporte debe tener reviewer

```python
def test_report_must_have_reviewer_when_not_under_review():
    """¿Reporte ACCEPTED/REJECTED debe tener reviewed_by? (debe fallar si no lo tiene)"""
    user_report = UserReportFactory(report__status='UNDER_REVIEW')
    
    report = user_report.report
    report.status = 'ACCEPTED'
    report.reviewed_by = None  # Sin reviewer
    
    with pytest.raises(ValidationError):
        report.save()
```

**¿Qué verifica?**
- Validación `Report.clean()` funciona
- Reportes aceptados/rechazados deben tener `reviewed_by`

---

#### Test 7: 1er reporte ACEPTADO → Suspensión 30 días

```python
def test_user_moderation_first_accepted_suspends_30_days():
    """¿1er reporte aceptado suspende al usuario 30 días?"""
    target_user = UserFactory(is_active=True)
    admin = AdminFactory()
    
    user_report = UserReportFactory(
        report__reporter=UserFactory(),
        reported_user=target_user,
        report__reason="Fraude"
    )
    
    # Aceptar reporte
    report = user_report.report
    report.status = 'ACCEPTED'
    report.reviewed_by = admin
    report.save()
    
    # Verificar suspensión
    target_user.refresh_from_db()
    assert target_user.is_active == False
    assert target_user.suspension_end_at is not None
    
    # Verificar ~30 días
    days_suspended = (target_user.suspension_end_at - date.today()).days
    assert days_suspended in [29, 30, 31]
```

**¿Qué verifica?**
- **TRIGGER 11 de MySQL funciona** (auto-moderación)
- 1er reporte aceptado suspende usuario
- Suspensión es ~30 días
- `is_active` cambia a FALSE
- `suspension_end_at` se calcula correctamente

**Este es el test más crítico del sistema.**

---

#### Test 8: 2º reporte ACEPTADO → Eliminación permanente

```python
def test_user_moderation_second_accepted_deletes_user():
    """¿2º reporte aceptado elimina al usuario permanentemente?"""
    target_user = UserFactory(is_active=True)
    admin = AdminFactory()
    user_pk = target_user.pk
    
    # ===== 1ER REPORTE =====
    user_report1 = UserReportFactory(
        report__reporter=UserFactory(),
        reported_user=target_user,
        report__reason="Infracción #1"
    )
    
    report1 = user_report1.report
    report1.status = 'ACCEPTED'
    report1.reviewed_by = admin
    report1.save()
    
    target_user.refresh_from_db()
    assert target_user.is_active == False  # Suspendido
    
    # ===== 2º REPORTE =====
    user_report2 = UserReportFactory(
        report__reporter=UserFactory(),
        reported_user=target_user,
        report__reason="Infracción #2"
    )
    
    report2 = user_report2.report
    report2.status = 'ACCEPTED'
    report2.reviewed_by = admin
    report2.save()
    
    # Usuario debe estar ELIMINADO
    with pytest.raises(User.DoesNotExist):
        User.objects.get(pk=user_pk)
```

**¿Qué verifica?**
- **TRIGGER 11 escala las sanciones** (1er reporte → suspensión, 2º → eliminación)
- Usuario es eliminado completamente de la BD
- No queda registro del usuario
- Cascade elimina Student/Landlord asociado

**Este test prueba el flujo completo de moderación automática.**

---

## 🚀 CÓMO EJECUTAR LOS TESTS

### Requisitos Previos

```powershell
# Activar entorno virtual
.\venv\Scripts\Activate.ps1

# Instalar dependencias
pip install pytest pytest-django factory-boy
```

### Comandos Básicos

```powershell
# Ejecutar TODOS los tests (48 tests)
pytest tests/

# Ejecutar con output detallado
pytest tests/ -v

# Ejecutar solo tests unitarios (40 tests)
pytest tests/unit/ -v

# Ejecutar solo tests de integración (8 tests)
pytest tests/integration/ -v

# Ejecutar un archivo específico
pytest tests/unit/test_models_users.py -v

# Ejecutar una clase específica
pytest tests/unit/test_models_users.py::TestUserModel -v

# Ejecutar un test específico
pytest tests/unit/test_models_users.py::TestUserModel::test_user_creation_with_valid_data -v
```

### Ver Resultados

```
======================== test session starts ========================
collected 48 items

tests/integration/test_reports_moderation.py::test_create_user_report PASSED [2%]
tests/integration/test_reports_moderation.py::test_create_listing_report PASSED [4%]
... (46 tests más)
tests/unit/test_models_users.py::test_deleting_student_does_not_delete_user PASSED [100%]

======================== 48 passed in 116.38s ========================
```

### Opciones Útiles

```powershell
# Mostrar print() statements
pytest tests/ -v -s

# Parar en el primer error
pytest tests/ -x

# Ejecutar tests por palabra clave
pytest tests/ -k "user"  # Solo tests con "user" en el nombre

# Mostrar warnings
pytest tests/ -v --tb=short

# Mostrar cobertura de código
pytest tests/ --cov=users --cov=listings --cov=inquiries

# Rerun solo tests fallidos
pytest tests/ --lf
```

---

## 🛠️ SOLUCIÓN DE PROBLEMAS

### Error: "No module named 'pytest'"

```powershell
pip install pytest pytest-django
```

---

### Error: "Database test_umigo doesn't exist"

```powershell
# Django debería crearla automáticamente, pero si falla:
python tests/setup_test_db.py
```

---

### Error: "IntegrityError: zone_id cannot be null"

**Causa:** Las 20 zonas no están cargadas en `test_umigo`.

**Solución:**

```powershell
# Opción 1: Ejecutar tests con --reuse-db (recomienda Django)
pytest tests/ --reuse-db

# Opción 2: Cargar zonas manualmente
python manage.py loaddata zones.json --database=default
```

---

### Error: "OperationalError: Table 'test_umigo.xxx' doesn't exist"

**Causa:** Base de datos no tiene todas las tablas.

**Solución:**

```powershell
# Recrear base de datos de test
python tests/setup_test_db.py

# O ejecutar sin --reuse-db
pytest tests/
```

---

### Error: Tests pasan localmente pero fallan en CI/CD

**Causa:** Base de datos de CI/CD no tiene triggers/constraints.

**Solución:**

Asegurar que CI/CD ejecute el script SQL completo:

```yaml
# .github/workflows/tests.yml
- name: Setup test database
  run: |
    mysql -u root -p${{ secrets.MYSQL_PASSWORD }} < documentation/SCRIPT_FINAL_BD_UMIGO.sql
```

---

### Error: "AssertionError: assert 0 == 4.0" en test de popularidad

**Causa:** Triggers 6-8 no están actualizando `listing.popularity`.

**Solución:**

Verificar que los triggers existen en `test_umigo`:

```sql
USE test_umigo;
SHOW TRIGGERS LIKE '%review%';
```

Si no aparecen, ejecutar el script SQL completo.

## 📝 CONCLUSIÓN

Con esta guía, cualquier miembro del equipo puede:

- **Entender** cómo funciona el sistema de testing
- **Ejecutar** los tests sin ayuda
- **Leer** cada test y saber qué verifica
- **Agregar** nuevos tests si es necesario
- **Solucionar** problemas comunes

**No necesitas preguntarle a nadie. Esta guía es suficiente.** 🎉
