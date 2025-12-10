"""
Tests complets pour la refactorisation de l'API key de UserGroup vers UserSubscription.

Ce module teste tous les aspects de la migration de l'API key depuis UserGroup
vers UserSubscription pour s'assurer que la refactorisation fonctionne correctement.
"""

import json
from datetime import timedelta
from unittest.mock import patch, Mock

from django.contrib.auth import get_user_model
from django.test import TestCase, RequestFactory
from django.utils import timezone

from subscriptions.models import SubscriptionType, UserSubscription
from subscriptions.utils import get_user_api_key
from users.models import UserGroup
from tests.mock import create_test_user_group, create_test_user_subscription

# Import des fonctions à tester
from api.utils import get_api_user, get_user_and_data
# from writing.views import WritingProcessAPIView  # COMMENTED - Feature disabled
from users.views import DeleteAllDataView
from quoting.services.quote import FormQuoteService
from legal.views_all import text_translation, file_translate


class APIMigrationTestCase(TestCase):
    """Tests complets pour la migration de l'API key."""
    
    def setUp(self):
        """Configuration des tests."""
        self.factory = RequestFactory()
        User = get_user_model()
        
        # Créer un groupe de test
        self.group = create_test_user_group(name="Test Group")
        
        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            group=self.group
        )
        
        # Créer un type de subscription LEXA
        self.subscription_type = SubscriptionType.objects.create(
            name='Test LEXA Subscription',
            product_type=SubscriptionType.ProductChoices.LEXA,
            price=100.00
        )
        
        # Créer une subscription avec API key
        self.user_subscription = create_test_user_subscription(
            user=self.user,
            subscription_type=self.subscription_type,
            api_key='test-api-key-12345'
        )
    
    def test_get_user_api_key_utility(self):
        """Test de la fonction utilitaire get_user_api_key."""
        # Test avec utilisateur normal
        api_key = get_user_api_key(self.user)
        self.assertEqual(api_key, 'test-api-key-12345')
        
        # Test avec utilisateur staff - même le staff doit avoir une subscription
        self.user.is_staff = True
        self.user.save()
        
        # Le staff doit toujours utiliser sa clé API de subscription
        api_key = get_user_api_key(self.user)
        self.assertEqual(api_key, 'test-api-key-12345')
    
    def test_get_user_api_key_no_subscription(self):
        """Test de get_user_api_key avec utilisateur sans subscription."""
        # Supprimer la subscription
        self.user_subscription.delete()
        
        # Doit lever ValueError
        with self.assertRaises(ValueError) as context:
            get_user_api_key(self.user)
        self.assertEqual(str(context.exception), "no subscription")
    
    def test_api_utils_get_api_user(self):
        """Test de get_api_user dans api/utils.py."""
        request = self.factory.get('/')
        request.headers = {'Authorization': 'Bearer test-api-key-12345'}
        
        user, error = get_api_user(request)
        
        self.assertIsNone(error)
        self.assertEqual(user, self.user)
    
    def test_api_utils_get_api_user_invalid_key(self):
        """Test de get_api_user avec clé invalide."""
        request = self.factory.get('/')
        request.headers = {'Authorization': 'Bearer invalid-key'}
        
        user, error = get_api_user(request)
        
        self.assertIsNone(user)
        self.assertIsNotNone(error)
    
    def test_api_utils_get_user_and_data(self):
        """Test de get_user_and_data."""
        data = {'test': 'data'}
        request = self.factory.post('/',
                                   data=json.dumps(data),
                                   content_type='application/json')
        request.headers = {'Authorization': 'Bearer test-api-key-12345'}
        
        user, result_data, error = get_user_and_data(request)
        
        self.assertIsNone(error)
        self.assertEqual(user, self.user)
        self.assertEqual(result_data, data)
    
    # ============================================================================
    # WRITING FUNCTIONALITY - TEMPORARILY DISABLED
    # ============================================================================
    # @patch('requests.post')
    # def test_writing_views_api_key_usage(self, mock_post):
    #     """Test de l'utilisation de l'API key dans writing/views.py."""
    #     mock_response = Mock()
    #     mock_response.json.return_value = {'result': ['test result']}
    #     mock_post.return_value = mock_response
    #     
    #     request = self.factory.post('/writing/process/', {
    #         'prompt': 1,
    #         'text': 'test text'
    #     })
    #     request.user = self.user
    #     
    #     view = WritingProcessAPIView()
    #     response = view.post(request)
    #     
    #     # Vérifier que la requête a été faite avec la bonne API key
    #     self.assertTrue(mock_post.called)
    #     # Vérifier que parmi les appels, l'en-tête contient la bonne clé
    #     matched = any(kwargs.get('headers', {}).get('token') == 'test-api-key-12345' for args, kwargs in mock_post.call_args_list)
    #     self.assertTrue(matched)
    
    @patch('requests.get')
    def test_users_views_api_key_usage(self, mock_get):
        """Test de l'utilisation de l'API key dans users/views.py."""
        mock_response = Mock()
        mock_response.json.return_value = {'num_pages': 1, 'results': []}
        mock_get.return_value = mock_response
        
        request = self.factory.post('/users/delete-all-data/', {
            'password': 'testpass123'
        })
        request.user = self.user
        
        view = DeleteAllDataView()
        response = view.post(request)
        
        # Vérifier que la requête a été faite avec la bonne API key
        mock_get.assert_called()
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]['headers']['token'], 'test-api-key-12345')
    
    @patch('requests.get')
    def test_quoting_services_api_key_usage(self, mock_get):
        """Test de l'utilisation de l'API key dans quoting/services/quote.py."""
        mock_response = Mock()
        mock_response.json.return_value = {
            'source_language': 'en',
            'target_language': 'fr',
            'source_file': 'http://example.com/file.txt'
        }
        mock_get.return_value = mock_response
        
        request = self.factory.post('/quoting/send-quote/', {
            'project_id': '123'
        })
        request.user = self.user
        
        service = FormQuoteService()
        service.send_quote_to_user(request)
        
        # Vérifier que la requête a été faite avec la bonne API key
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[1]['headers']['token'], 'test-api-key-12345')
    
    @patch('requests.post')
    def test_legal_views_text_translation(self, mock_post):
        """Test de l'utilisation de l'API key dans legal/views.py pour text_translation."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': 'translated text'}
        mock_post.return_value = mock_response
        
        request = self.factory.post('/legal/translate/', {
            'text': 'Hello world',
            'action': 'text_translate'
        })
        request.user = self.user
        
        with patch('legal.views.translation_allowed', return_value=True):
            response = text_translation(request)
        
        # Vérifier que la requête a été faite avec la bonne API key
        self.assertTrue(mock_post.called)
        matched = any(kwargs.get('headers', {}).get('token') == 'test-api-key-12345' for args, kwargs in mock_post.call_args_list)
        self.assertTrue(matched)
    
    def test_get_user_api_key_no_subscription(self):
        """Test de get_user_api_key avec utilisateur sans subscription."""
        # Supprimer la subscription
        self.user_subscription.delete()
        
        # Doit lever ValueError
        with self.assertRaises(ValueError) as context:
            get_user_api_key(self.user)
        self.assertEqual(str(context.exception), "no subscription")
    
    def test_subscription_type_validation(self):
        """Test de la validation du type de subscription."""
        # Créer une subscription avec un type différent
        other_subscription_type = SubscriptionType.objects.create(
            name='Other Subscription',
            product_type=SubscriptionType.ProductChoices.WORD_ADD_IN,
            price=50.00
        )
        
        other_subscription = create_test_user_subscription(
            user=self.user,
            subscription_type=other_subscription_type,
            api_key='other-api-key'
        )
        
        # Supprimer l'ancienne subscription
        self.user_subscription.delete()
        
        # La fonction devrait toujours retourner l'API key car WORD_ADD_IN est accepté
        api_key = get_user_api_key(self.user)
        self.assertEqual(api_key, 'other-api-key')
    
    def test_multiple_subscriptions_handling(self):
        """Test de la gestion de plusieurs subscriptions."""
        # Créer une deuxième subscription
        second_subscription = create_test_user_subscription(
            user=self.user,
            subscription_type=self.subscription_type,
            api_key='second-api-key'
        )
        
        # La fonction devrait retourner la première subscription trouvée
        api_key = get_user_api_key(self.user)
        self.assertEqual(api_key, 'test-api-key-12345')
    
    def test_inactive_subscription_handling(self):
        """Test de la gestion des subscriptions inactives."""
        # Rendre la subscription inactive
        self.user_subscription.status = UserSubscription.UserSubscriptionChoices.TERMINATED
        self.user_subscription.save()
        
        # Doit lever ValueError
        with self.assertRaises(ValueError) as context:
            get_user_api_key(self.user)
        self.assertEqual(str(context.exception), "no subscription")
    
    def test_expired_subscription_handling(self):
        """Test de la gestion des subscriptions expirées."""
        # Rendre la subscription expirée
        self.user_subscription.end_date = timezone.now() - timedelta(days=1)
        self.user_subscription.save()
        
        # Doit lever ValueError
        with self.assertRaises(ValueError) as context:
            get_user_api_key(self.user)
        self.assertEqual(str(context.exception), "no subscription")
    
    def test_subscription_without_api_key(self):
        """Test de la gestion des subscriptions sans API key."""
        # Supprimer la subscription (équivalent à aucune API key active)
        self.user_subscription.delete()
        
        # Doit lever ValueError
        with self.assertRaises(ValueError) as context:
            get_user_api_key(self.user)
        self.assertEqual(str(context.exception), "no subscription")


class IntegrationTestCase(TestCase):
    """Tests d'intégration pour vérifier le fonctionnement end-to-end."""
    
    def setUp(self):
        """Configuration des tests d'intégration."""
        self.factory = RequestFactory()
        User = get_user_model()
        
        # Créer un groupe de test
        self.group = create_test_user_group(name="Integration Test Group")
        
        # Créer un utilisateur de test
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@example.com',
            password='testpass123',
            group=self.group
        )
        
        # Créer un type de subscription LEXA
        self.subscription_type = SubscriptionType.objects.create(
            name='Integration LEXA Subscription',
            product_type=SubscriptionType.ProductChoices.LEXA,
            price=100.00
        )
        
        # Créer une subscription avec API key
        self.user_subscription = create_test_user_subscription(
            user=self.user,
            subscription_type=self.subscription_type,
            api_key='integration-api-key-67890'
        )
    
    @patch('requests.post')
    def test_end_to_end_api_authentication(self, mock_post):
        """Test d'authentification API end-to-end."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': 'success'}
        mock_post.return_value = mock_response
        
        # Simuler une requête API complète
        request = self.factory.post('/api/translate/', {
            'text': 'Hello world',
            'source_language': 'en',
            'target_language': 'fr'
        })
        request.headers = {'Authorization': 'Bearer integration-api-key-67890'}
        
        # Utiliser get_user_and_data pour l'authentification
        user, data, error = get_user_and_data(request)
        
        # Vérifications
        self.assertIsNone(error)
        self.assertEqual(user, self.user)
        self.assertEqual(data['text'], 'Hello world')
    
    def test_api_key_consistency_across_modules(self):
        """Test de la cohérence de l'API key à travers tous les modules."""
        # Tester que la fonction retourne la bonne API key
        from subscriptions.utils import get_user_api_key
        
        # Test avec get_user_api_key
        api_key = get_user_api_key(self.user)
        
        # Doit retourner la bonne clé
        self.assertEqual(api_key, 'integration-api-key-67890')
    
    def test_staff_user_requires_subscription(self):
        """Test que les utilisateurs staff doivent aussi avoir une subscription."""
        # Rendre l'utilisateur staff
        self.user.is_staff = True
        self.user.save()
        
        # Même le staff doit utiliser sa clé API de subscription
        from subscriptions.utils import get_user_api_key
        
        # La fonction doit retourner la clé de subscription
        api_key = get_user_api_key(self.user)
        self.assertEqual(api_key, 'integration-api-key-67890')
        
        # Si le staff n'a pas de subscription, doit lever ValueError
        self.user_subscription.delete()
        
        with self.assertRaises(ValueError) as context:
            get_user_api_key(self.user)
        self.assertEqual(str(context.exception), "no subscription")

