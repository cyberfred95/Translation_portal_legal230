"""
Tests pour le service de génération de clés API.

Ce module teste la génération de clés API locales et la vérification d'unicité.
"""

from django.test import TestCase
from django.contrib.auth import get_user_model

from subscriptions.models import UserSubscription, SubscriptionType
from subscriptions.services.api_key_generator import APIKeyGenerator, APIKeyService


class APIKeyGeneratorTestCase(TestCase):
    """Tests pour la classe APIKeyGenerator."""
    
    def setUp(self):
        """Configuration des tests."""
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.subscription_type = SubscriptionType.objects.create(
            name='Test Subscription',
            product_type=SubscriptionType.ProductChoices.LEXA,
            price=100.00
        )
    
    def _assert_uuid_format(self, key: str):
        """Helper pour vérifier le format UUID d'une clé."""
        self.assertIsNotNone(key)
        self.assertEqual(len(key), 36)
        
        parts = key.split('-')
        self.assertEqual(len(parts), 5)
        self.assertEqual(len(parts[0]), 8)
        self.assertEqual(len(parts[1]), 4)
        self.assertEqual(len(parts[2]), 4)
        self.assertEqual(len(parts[3]), 4)
        self.assertEqual(len(parts[4]), 12)
        
        # Vérifier que tous les caractères sont hexadécimaux (minuscules)
        full_key_without_dashes = key.replace('-', '')
        self.assertTrue(all(c in APIKeyGenerator.HEXADECIMAL_CHARACTERS for c in full_key_without_dashes))
    
    def test_generate_key_uuid_format(self):
        """Test de génération d'une clé au format UUID."""
        key = APIKeyGenerator.generate_key()
        self._assert_uuid_format(key)
    
    def test_generate_key_uuid_format_multiple(self):
        """Test que plusieurs clés générées ont toutes le bon format UUID."""
        for _ in range(10):
            key = APIKeyGenerator.generate_key()
            self._assert_uuid_format(key)
    
    def test_is_key_unique_empty_key(self):
        """Test que une clé vide n'est pas considérée comme unique."""
        self.assertFalse(APIKeyGenerator.is_key_unique(""))
        self.assertFalse(APIKeyGenerator.is_key_unique(None))
    
    def test_is_key_unique_new_key(self):
        """Test qu'une nouvelle clé est considérée comme unique."""
        key = APIKeyGenerator.generate_key()
        self.assertTrue(APIKeyGenerator.is_key_unique(key))
    
    def test_is_key_unique_existing_key(self):
        """Test qu'une clé existante n'est pas considérée comme unique."""
        # Créer une subscription avec une clé API
        subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            api_key="test-api-key-12345",
            start_date="2024-01-01",
            end_date="2025-12-31"
        )
        
        # Vérifier que la clé existante n'est pas unique
        self.assertFalse(APIKeyGenerator.is_key_unique("test-api-key-12345"))
        
        # Mais elle est unique si on exclut cette subscription
        self.assertTrue(
            APIKeyGenerator.is_key_unique(
                "test-api-key-12345",
                exclude_subscription_id=subscription.id
            )
        )
    
    def test_generate_unique_key_success(self):
        """Test de génération d'une clé unique au format UUID."""
        key = APIKeyGenerator.generate_unique_key()
        
        self._assert_uuid_format(key)
        self.assertTrue(APIKeyGenerator.is_key_unique(key))
    
    def test_generate_unique_key_with_exclusion(self):
        """Test de génération d'une clé unique avec exclusion."""
        # Créer une subscription avec une clé API
        subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            api_key="existing-key-12345",
            start_date="2024-01-01",
            end_date="2025-12-31"
        )
        
        # Générer une clé unique en excluant cette subscription
        key = APIKeyGenerator.generate_unique_key(
            exclude_subscription_id=subscription.id
        )
        
        self.assertIsNotNone(key)
        self.assertNotEqual(key, "existing-key-12345")
        self.assertTrue(
            APIKeyGenerator.is_key_unique(
                key,
                exclude_subscription_id=subscription.id
            )
        )


class APIKeyServiceTestCase(TestCase):
    """Tests pour la classe APIKeyService."""
    
    def setUp(self):
        """Configuration des tests."""
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.subscription_type = SubscriptionType.objects.create(
            name='Test Subscription',
            product_type=SubscriptionType.ProductChoices.LEXA,
            price=100.00
        )
    
    def _assert_uuid_format(self, key: str):
        """Helper pour vérifier le format UUID d'une clé."""
        self.assertIsNotNone(key)
        self.assertEqual(len(key), 36)
        
        parts = key.split('-')
        self.assertEqual(len(parts), 5)
        self.assertEqual(len(parts[0]), 8)
        self.assertEqual(len(parts[1]), 4)
        self.assertEqual(len(parts[2]), 4)
        self.assertEqual(len(parts[3]), 4)
        self.assertEqual(len(parts[4]), 12)
        
        # Vérifier que tous les caractères sont hexadécimaux (minuscules)
        full_key_without_dashes = key.replace('-', '')
        self.assertTrue(all(c in APIKeyGenerator.HEXADECIMAL_CHARACTERS for c in full_key_without_dashes))
    
    def test_create_api_key_for_subscription_new(self):
        """Test de création d'une clé API pour une nouvelle subscription."""
        subscription = UserSubscription(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            start_date="2024-01-01",
            end_date="2025-12-31"
        )
        
        # Générer la clé avant de sauvegarder (pas d'ID encore)
        key = APIKeyService.create_api_key_for_subscription(subscription)
        
        self._assert_uuid_format(key)
        self.assertTrue(APIKeyGenerator.is_key_unique(key))
    
    def test_create_api_key_for_subscription_existing(self):
        """Test de création d'une clé API pour une subscription existante."""
        # Créer une subscription avec une clé existante
        existing_subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            api_key="existing-key-12345",
            start_date="2024-01-01",
            end_date="2025-12-31"
        )
        
        # Créer une nouvelle subscription
        new_subscription = UserSubscription(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            start_date="2024-01-01",
            end_date="2025-12-31"
        )
        
        # Générer une clé pour la nouvelle subscription
        key = APIKeyService.create_api_key_for_subscription(new_subscription)
        
        self.assertIsNotNone(key)
        self.assertNotEqual(key, "existing-key-12345")
        self.assertTrue(APIKeyGenerator.is_key_unique(key))
    


class UserSubscriptionAPIGenerationTestCase(TestCase):
    """Tests d'intégration pour la génération de clés API dans UserSubscription."""
    
    def setUp(self):
        """Configuration des tests."""
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.subscription_type = SubscriptionType.objects.create(
            name='Test Subscription',
            product_type=SubscriptionType.ProductChoices.LEXA,
            price=100.00
        )
    
    def _assert_uuid_format(self, key: str):
        """Helper pour vérifier le format UUID d'une clé."""
        self.assertIsNotNone(key)
        self.assertEqual(len(key), 36)
        
        parts = key.split('-')
        self.assertEqual(len(parts), 5)
        self.assertEqual(len(parts[0]), 8)
        self.assertEqual(len(parts[1]), 4)
        self.assertEqual(len(parts[2]), 4)
        self.assertEqual(len(parts[3]), 4)
        self.assertEqual(len(parts[4]), 12)
        
        # Vérifier que tous les caractères sont hexadécimaux (minuscules)
        full_key_without_dashes = key.replace('-', '')
        self.assertTrue(all(c in APIKeyGenerator.HEXADECIMAL_CHARACTERS for c in full_key_without_dashes))
    
    def test_auto_generate_api_key_on_save(self):
        """Test que la clé API est générée automatiquement lors de la sauvegarde."""
        subscription = UserSubscription(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            start_date="2024-01-01",
            end_date="2025-12-31"
        )
        
        # Sauvegarder - la clé devrait être générée automatiquement
        subscription.save()
        
        self.assertIsNotNone(subscription.api_key)
        self._assert_uuid_format(subscription.api_key)
        self.assertTrue(APIKeyGenerator.is_key_unique(subscription.api_key))
    
    def test_no_auto_generate_for_inactive_subscription(self):
        """Test qu'aucune clé n'est générée pour une subscription inactive."""
        subscription = UserSubscription(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.TERMINATED,
            start_date="2024-01-01",
            end_date="2025-12-31"
        )
        
        subscription.save()
        
        # La clé ne devrait pas être générée pour une subscription inactive
        self.assertIsNone(subscription.api_key) or self.assertEqual(subscription.api_key, "")
    
    def test_no_auto_generate_if_key_exists(self):
        """Test qu'aucune nouvelle clé n'est générée si une clé existe déjà."""
        subscription = UserSubscription.objects.create(
            user=self.user,
            subscription=self.subscription_type,
            status=UserSubscription.UserSubscriptionChoices.ACTIVE,
            api_key="existing-key-12345",
            start_date="2024-01-01",
            end_date="2025-12-31"
        )
        
        original_key = subscription.api_key
        
        # Sauvegarder à nouveau
        subscription.save()
        
        # La clé ne devrait pas avoir changé
        self.assertEqual(subscription.api_key, original_key)
    
    def test_unique_keys_for_multiple_subscriptions(self):
        """Test que plusieurs subscriptions obtiennent des clés uniques."""
        subscriptions = []
        for i in range(5):
            subscription = UserSubscription(
                user=self.user,
                subscription=self.subscription_type,
                status=UserSubscription.UserSubscriptionChoices.ACTIVE,
                start_date="2024-01-01",
                end_date="2025-12-31"
            )
            subscription.save()
            subscriptions.append(subscription)
        
        # Vérifier que toutes les clés sont uniques
        keys = [sub.api_key for sub in subscriptions]
        self.assertEqual(len(keys), len(set(keys)), "Toutes les clés doivent être uniques")
        
        # Vérifier que chaque clé est unique dans la base de données
        for subscription in subscriptions:
            self.assertTrue(
                APIKeyGenerator.is_key_unique(
                    subscription.api_key,
                    exclude_subscription_id=subscription.id
                )
            )

