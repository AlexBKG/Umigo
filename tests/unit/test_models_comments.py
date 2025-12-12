# tests/unit/test_models_comments.py
"""
Tests para Comentarios anidados (3 tests)
PRIORIDAD: MEDIA
TIEMPO ESTIMADO: 1.5 horas
DÍA: Martes (14:00-15:30)
"""

import pytest
from django.core.exceptions import ValidationError
from tests.factories.listings import ListingFactory, CommentFactory
from tests.factories.users import UserFactory


@pytest.mark.django_db
class TestCommentModel:
    """Tests para el modelo Comment"""

    def test_comment_creation(self):
        """✅ Comentario se crea correctamente en un listing"""
        comment = CommentFactory()
        
        assert comment.id is not None
        assert comment.listing is not None
        assert comment.author is not None
        assert comment.text is not None
        assert len(comment.text) <= 800
        assert comment.parent is None  # Comentario raíz

    def test_comment_reply_same_listing(self):
        """✅ Respuesta (reply) debe pertenecer al mismo listing que el parent"""
        listing = ListingFactory()
        user = UserFactory()
        
        # Crear comentario padre
        parent_comment = CommentFactory(listing=listing, author=user)
        
        # Crear respuesta en el MISMO listing (debe funcionar)
        reply = CommentFactory(
            listing=listing, 
            author=user, 
            parent=parent_comment
        )
        
        assert reply.parent == parent_comment
        assert reply.listing == listing
        assert reply.listing == parent_comment.listing

    def test_comment_reply_different_listing_fails(self):
        """✅ No se puede responder a un comentario de OTRO listing
        
        Este test verifica que no se pueda crear un reply en un listing diferente
        al del parent comment. La validación se hace en Comment.clean().
        """
        listing1 = ListingFactory()
        listing2 = ListingFactory()
        user = UserFactory()
        
        parent_comment = CommentFactory(listing=listing1, author=user)
        
        with pytest.raises(ValidationError):
            reply = CommentFactory.build(
                listing=listing2,
                author=user,
                parent=parent_comment
            )
            reply.full_clean()


# ==============================================================================
# INSTRUCCIONES PARA EJECUTAR
# ==============================================================================
"""
1. Ejecutar todos los tests:
   pytest tests/unit/test_models_comments.py -v

2. Si test_comment_reply_different_listing_fails falla:
   - Verificar que Comment.clean() valida que parent.listing == self.listing
   - Si la validación está en la vista, mover test a integration/
   - O agregar la validación al modelo:
   
   def clean(self):
       if self.parent and self.parent.listing != self.listing:
           raise ValidationError(
               "El comentario padre debe pertenecer al mismo listing"
           )

3. Ver cobertura:
   pytest tests/unit/test_models_comments.py --cov=listings.models --cov-report=term-missing
"""
