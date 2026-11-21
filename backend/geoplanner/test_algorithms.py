"""Unit tests for the routing algorithms (no database, no network)."""

import itertools
import random

from django.test import SimpleTestCase

from .algorithms import _nearest_neighbour, haversine_distance, solve_tsp


def tour_length(depot, ordered):
    pts = [depot] + list(ordered) + [depot]
    return sum(haversine_distance(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


class HaversineTest(SimpleTestCase):

    def test_zero_distance(self):
        p = {'latitude': 51.1, 'longitude': 17.03}
        self.assertEqual(haversine_distance(p, p), 0)

    def test_warsaw_krakow(self):
        warsaw = {'latitude': 52.2297, 'longitude': 21.0122}
        krakow = {'latitude': 50.0647, 'longitude': 19.9450}
        # great-circle distance is ~252 km
        self.assertAlmostEqual(haversine_distance(warsaw, krakow) / 1000, 252, delta=3)

    def test_symmetry(self):
        a = {'latitude': 54.35, 'longitude': 18.65}
        b = {'latitude': 51.11, 'longitude': 17.04}
        self.assertAlmostEqual(haversine_distance(a, b), haversine_distance(b, a))


class SolveTspTest(SimpleTestCase):

    depot = {'latitude': 51.1079, 'longitude': 17.0385}

    def random_jobs(self, n, seed):
        rnd = random.Random(seed)
        return [{'id': i,
                 'latitude': 51.1079 + rnd.uniform(-0.1, 0.1),
                 'longitude': 17.0385 + rnd.uniform(-0.1, 0.1)} for i in range(n)]

    def test_edge_cases(self):
        self.assertEqual(solve_tsp(self.depot, []), [])
        one = [{'id': 1, 'latitude': 51.0, 'longitude': 17.0}]
        self.assertEqual(solve_tsp(self.depot, one), one)

    def test_visits_every_job_exactly_once(self):
        jobs = self.random_jobs(12, seed=1)
        result = solve_tsp(self.depot, jobs, time_limit_s=1)
        self.assertEqual(sorted(j['id'] for j in result), list(range(12)))

    def test_optimal_on_small_instance(self):
        """For 7 jobs the brute-force optimum (5040 tours) is the reference."""
        jobs = self.random_jobs(7, seed=2)
        best = min(tour_length(self.depot, p) for p in itertools.permutations(jobs))
        got = tour_length(self.depot, solve_tsp(self.depot, jobs, time_limit_s=1))
        # OR-Tools works on distances rounded to whole metres
        self.assertLessEqual(got, best + len(jobs) + 1)

    def test_not_worse_than_nearest_neighbour(self):
        jobs = self.random_jobs(25, seed=3)
        ortools = tour_length(self.depot, solve_tsp(self.depot, jobs, time_limit_s=1))
        greedy = tour_length(self.depot, _nearest_neighbour(self.depot, jobs))
        self.assertLessEqual(ortools, greedy + 1)
