# tests/unit/test_models_favorites.py
"""
Tests para Favoritos (2 tests)
PRIORIDAD: MEDIA
TIEMPO ESTIMADO: 1 hora
DÍA: Martes (15:30-16:30)
"""

import pytest
from django.db import IntegrityError
from tests.factories.listings import ListingFactory, FavoriteFactory
from tests.factories.users import StudentFactory


@pytest.mark.django_db
class TestFavoriteModel:
    """Tests para el modelo Favorite (ManyToMany Listing ↔ Student)"""

    def test_favorite_creation(self):
        """✅ Estudiante marca listing como favorito correctamente"""
        favorite = FavoriteFactory()
        
        assert favorite.id is not None
        assert favorite.student is not None
        assert favorite.listing is not None
        assert favorite.created_at is not None
        
        # Verificar relación inversa
        assert favorite.listing in favorite.student.favorite_listings.all()

    def test_favorite_unique_per_student_listing(self):
        """✅ Un estudiante no puede marcar el mismo listing 2 veces (unique_together)"""
        student = StudentFactory()
        listing = ListingFactory()
        
        # Primer favorito (OK)
        favorite1 = FavoriteFactory(student=student, listing=listing)
        assert favorite1.id is not None
        
        # Segundo favorito del MISMO estudiante en el MISMO listing (debe fallar)
        with pytest.raises(IntegrityError):
            favorite2 = FavoriteFactory(student=student, listing=listing)


# ==============================================================================
# INSTRUCCIONES PARA EJECUTAR
# ==============================================================================
"""
1. Ejecutar todos los tests:
   pytest tests/unit/test_models_favorites.py -v

2. Ver cobertura:
   pytest tests/unit/test_models_favorites.py --cov=listings.models --cov-report=term-missing

3. BONUS (si hay tiempo):
   - Test para verificar que al borrar Student, se borran sus favoritos (CASCADE)
   - Test para verificar que favoritos actualizan popularidad del listing
"""
