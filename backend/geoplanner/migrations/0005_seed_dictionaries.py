"""
Data migration: dictionary tables (route types, vehicle types, route statuses).

Without these rows a fresh database cannot create routes or run `seed_db`.
get_or_create keeps it safe for databases where the values were added by hand.
On an empty database the IDs follow the order below (TSP = 1, Draft = 1),
which is what the frontend expects when it creates a TSP route.
"""

from django.db import migrations

ROUTE_TYPES = ["TSP", "VRP"]
VEHICLE_TYPES = ["Van", "Truck", "Bike"]
ROUTE_STATUSES = ["Draft", "Active", "Archived"]


def seed(apps, schema_editor):
    for model_name, names in [
        ("RouteType", ROUTE_TYPES),
        ("VehicleType", VEHICLE_TYPES),
        ("RouteStatus", ROUTE_STATUSES),
    ]:
        model = apps.get_model("geoplanner", model_name)
        for name in names:
            model.objects.get_or_create(name=name)


def unseed(apps, schema_editor):
    # leave the dictionaries in place - routes may reference them
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("geoplanner", "0004_vehicle_photo"),
    ]

    operations = [
        migrations.RunPython(seed, unseed),
    ]
