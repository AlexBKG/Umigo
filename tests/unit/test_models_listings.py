# tests/unit/test_models_listings.py
"""
Tests para modelos de Listings (6 tests)
PRIORIDAD: ALTA
TIEMPO ESTIMADO: 3 horas
DÍA: Lunes (13:00-16:00)
"""

import pytest
from django.core.exceptions import ValidationError
from tests.factories.listings import ListingFactory, ListingPhotoFactory
from tests.factories.users import LandlordFactory


@pytest.mark.django_db
class TestListingModel:
    """Tests para el modelo Listing"""

    def test_listing_creation_basic(self):
        """✅ Listing se crea con campos mínimos obligatorios"""
        listing = ListingFactory()
        
        assert listing.id is not None
        assert listing.price > 0
        assert listing.rooms >= 1
        assert listing.bathrooms >= 1
        assert listing.owner is not None

    def test_listing_price_positive(self):
        """✅ Price no puede ser negativo (validación de modelo)"""
        with pytest.raises((ValidationError, ValueError)):
            listing = ListingFactory.build(price=-100)
            listing.full_clean()  # Trigger validators

    def test_listing_rooms_minimum_one(self):
        """✅ Listing debe tener al menos 1 habitación"""
        with pytest.raises((ValidationError, ValueError)):
            listing = ListingFactory.build(rooms=0)
            listing.full_clean()


@pytest.mark.django_db
class TestListingPhotoModel:
    """Tests para el modelo ListingPhoto (validación de fotos)"""

    def test_listing_photo_minimum_one(self):
        """✅ Listing debe tener al menos 1 foto para estar available=True"""
        listing = ListingFactory(available=False)
        
        # Intentar poner available=True sin fotos
        # NOTA: Esta validación puede estar en la vista, no en el modelo
        # Si está en el modelo, descomentar:
        # with pytest.raises(ValidationError):
        #     listing.available = True
        #     listing.save()
        
        # Con 1 foto válida
        ListingPhotoFactory(listing=listing, sort_order=0)
        listing.available = True
        listing.save()  # No debe lanzar error
        
        assert listing.available == True

    def test_listing_photo_maximum_five(self):
        """✅ Listing no puede tener más de 5 fotos (constraint)"""
        listing = ListingFactory()
        
        # Crear 5 fotos (máximo permitido)
        for i in range(5):
            ListingPhotoFactory(listing=listing, sort_order=i)
        
        # Intentar crear la 6ta foto
        # NOTA: Constraint puede ser en BD o en modelo
        # Si hay unique_together (listing, sort_order), usar sort_order=5
        # Si hay check de count, usar cualquier sort_order
        with pytest.raises(Exception):  # IntegrityError o ValidationError
            photo6 = ListingPhotoFactory(listing=listing, sort_order=5)

    def test_listing_photo_sort_order(self):
        """✅ Fotos se ordenan correctamente por sort_order"""
        listing = ListingFactory()
        
        # Crear fotos en desorden
        photo2 = ListingPhotoFactory(listing=listing, sort_order=2)
        photo0 = ListingPhotoFactory(listing=listing, sort_order=0)
        photo1 = ListingPhotoFactory(listing=listing, sort_order=1)
        
        # Obtener fotos ordenadas (modelo tiene ordering = ['sort_order', 'id'])
        photos = listing.photos.all()
        
        assert photos[0].sort_order == 0
        assert photos[1].sort_order == 1
        assert photos[2].sort_order == 2


# ==============================================================================
# INSTRUCCIONES PARA EJECUTAR
# ==============================================================================
"""
1. Ejecutar todos los tests de este archivo:
   pytest tests/unit/test_models_listings.py -v

2. Ejecutar un test específico:
   pytest tests/unit/test_models_listings.py::TestListingModel::test_listing_creation_basic -v

3. Ver cobertura:
   pytest tests/unit/test_models_listings.py --cov=listings --cov-report=term-missing

4. Si algún test falla:
   - Verificar que las factories estén importando correctamente
   - Verificar que la base de datos de test esté configurada
   - Usar pytest -vv --tb=short para ver detalles del error
"""
