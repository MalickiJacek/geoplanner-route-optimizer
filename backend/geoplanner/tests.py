from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from .models import Depot, Job, Vehicle, VehicleType


class JobModelTest(TestCase):
    """Testy modelu Job — czy dane poprawnie zapisują się w bazie."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='Test1234!')

    def test_job_create(self):
        job = Job.objects.create(
            user=self.user,
            address='ul. Testowa 1, Warszawa',
            job_code='JOB-001',
            latitude=52.2297,
            longitude=21.0122,
            demand=10,
        )
        self.assertEqual(job.address, 'ul. Testowa 1, Warszawa')
        self.assertEqual(job.job_code, 'JOB-001')
        self.assertEqual(job.demand, 10)
        self.assertTrue(job.is_active)  # domyślnie aktywny

    def test_job_str(self):
        job = Job.objects.create(user=self.user, address='ul. Kowalska 5, Kraków')
        self.assertEqual(str(job), 'ul. Kowalska 5, Kraków')


class DepotModelTest(TestCase):
    """Testy modelu Depot."""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='Test1234!')

    def test_depot_create(self):
        depot = Depot.objects.create(
            user=self.user,
            name='Magazyn Główny',
            address='ul. Przemysłowa 10, Warszawa',
            latitude=52.2297,
            longitude=21.0122,
        )
        self.assertEqual(depot.name, 'Magazyn Główny')
        self.assertEqual(depot.latitude, 52.2297)
        self.assertTrue(depot.is_active)

    def test_depot_str(self):
        depot = Depot.objects.create(
            user=self.user, name='Baza Kraków',
            address='ul. Floriańska 1', latitude=50.06, longitude=19.94,
        )
        self.assertEqual(str(depot), 'Baza Kraków')


class JobsAPITest(TestCase):
    """Testy endpointu /api/jobs/ — autentykacja i izolacja danych."""

    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='user1', password='Test1234!')
        self.user2 = User.objects.create_user(username='user2', password='Test1234!')

        # Job użytkownika 1
        self.job1 = Job.objects.create(
            user=self.user1, address='ul. Testowa 1', latitude=52.23, longitude=21.01
        )
        # Job użytkownika 2
        self.job2 = Job.objects.create(
            user=self.user2, address='ul. Testowa 2', latitude=52.24, longitude=21.02
        )

    def test_jobs_unauthenticated_returns_401(self):
        """Niezalogowany użytkownik nie może widzieć jobów."""
        response = self.client.get('/api/jobs/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_jobs_authenticated_returns_200(self):
        """Zalogowany użytkownik otrzymuje listę swoich jobów."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/api/jobs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_user_sees_only_own_jobs(self):
        """Użytkownik widzi tylko swoje joby, nie cudze."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get('/api/jobs/')
        addresses = [job['address'] for job in response.data]

        self.assertIn('ul. Testowa 1', addresses)   # swój job — widzi
        self.assertNotIn('ul. Testowa 2', addresses) # cuzy job — nie widzi

    def test_create_job(self):
        """Zalogowany użytkownik może dodać nowy job."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.post('/api/jobs/', {
            'address': 'ul. Nowa 99, Warszawa',
            'latitude': 52.25,
            'longitude': 21.05,
            'demand': 5,
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Job.objects.filter(user=self.user1).count(), 2)


class DepotsAPITest(TestCase):
    """Testy endpointu /api/depots/."""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='Test1234!')

    def test_depots_unauthenticated_returns_401(self):
        response = self.client.get('/api/depots/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_depots_authenticated_returns_200(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get('/api/depots/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
