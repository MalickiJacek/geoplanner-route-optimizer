"""API tests for creating and solving routes (POST /api/routes/{id}/solve/)."""

from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient

from .models import Depot, Job, Route, RouteStatus, RouteStop, RouteType, VehicleType


class DictionariesTest(TestCase):
    """Data migration 0005 fills the dictionary tables on a fresh database."""

    def test_dictionaries_seeded(self):
        self.assertEqual(set(RouteType.objects.values_list('name', flat=True)), {'TSP', 'VRP'})
        self.assertTrue(VehicleType.objects.exists())
        self.assertIn('Draft', RouteStatus.objects.values_list('name', flat=True))


@override_settings(TSP_TIME_LIMIT_S=1)
class SolveRouteAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='planner', password='Test1234!')
        self.other = User.objects.create_user(username='other', password='Test1234!')
        self.client.force_authenticate(user=self.user)

        self.depot = Depot.objects.create(user=self.user, name='Depot', address='Depot St 1',
                                          latitude=51.1079, longitude=17.0385)
        coords = [(51.12, 17.01), (51.09, 17.06), (51.13, 17.07), (51.08, 17.00)]
        self.jobs = [Job.objects.create(user=self.user, address=f'Job {i}', latitude=la, longitude=lo)
                     for i, (la, lo) in enumerate(coords)]
        self.route = Route.objects.create(
            user=self.user, depot=self.depot, name='Test route',
            route_type=RouteType.objects.get(name='TSP'),
            route_status=RouteStatus.objects.get(name='Draft'),
        )

    def solve(self, job_ids, route=None):
        route = route or self.route
        return self.client.post(f'/api/routes/{route.id}/solve/', {'job_ids': job_ids}, format='json')

    def test_solve_creates_ordered_stops_and_distance(self):
        res = self.solve([j.id for j in self.jobs])
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        stops = res.data['stops']
        self.assertEqual([s['sequence'] for s in stops], [1, 2, 3, 4])
        self.assertEqual({s['job'] for s in stops}, {j.id for j in self.jobs})
        self.assertGreater(res.data['total_distance_km'], 0)

    def test_resolve_replaces_previous_stops(self):
        self.solve([j.id for j in self.jobs])
        self.solve([j.id for j in self.jobs[:2]])
        self.assertEqual(RouteStop.objects.filter(route=self.route).count(), 2)

    def test_missing_job_ids_returns_400(self):
        self.assertEqual(self.solve([]).status_code, status.HTTP_400_BAD_REQUEST)

    def test_job_without_coordinates_returns_400(self):
        job = Job.objects.create(user=self.user, address='Not geocoded yet')
        self.assertEqual(self.solve([job.id]).status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_use_other_users_jobs(self):
        foreign = Job.objects.create(user=self.other, address='Foreign', latitude=51.1, longitude=17.0)
        res = self.solve([self.jobs[0].id, foreign.id])
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertNotIn(foreign.id, {s['job'] for s in res.data['stops']})

    def test_cannot_solve_other_users_route(self):
        other_depot = Depot.objects.create(user=self.other, name='D', address='A',
                                           latitude=51.0, longitude=17.0)
        other_route = Route.objects.create(
            user=self.other, depot=other_depot, name='Not mine',
            route_type=RouteType.objects.get(name='TSP'),
            route_status=RouteStatus.objects.get(name='Draft'),
        )
        res = self.solve([self.jobs[0].id], route=other_route)
        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
