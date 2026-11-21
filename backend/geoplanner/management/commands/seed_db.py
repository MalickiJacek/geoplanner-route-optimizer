import io
import random

from django.contrib.auth.models import User
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from faker import Faker
from PIL import Image, ImageDraw
from geoplanner.models import Depot, Job, Vehicle, VehicleType

fake = Faker('pl_PL')

# Użytkownicy testowi
SEED_USERS = [
    {'username': 'jan_kowalski',      'email': 'jan@example.com',   'password': 'Test1234!'},
    {'username': 'anna_nowak',        'email': 'anna@example.com',  'password': 'Test1234!'},
    {'username': 'piotr_wisniewski',  'email': 'piotr@example.com', 'password': 'Test1234!'},
]

# Depoty dla poszczególnych użytkowników
DEPOTS = {
    'jan_kowalski': [
        {'name': 'Magazyn Warszawa',  'address': 'ul. Marszałkowska 1, Warszawa',  'lat': 52.2297, 'lon': 21.0122},
        {'name': 'Oddział Łódź',      'address': 'ul. Piotrkowska 100, Łódź',      'lat': 51.7592, 'lon': 19.4560},
    ],
    'anna_nowak': [
        {'name': 'Baza Kraków',       'address': 'ul. Floriańska 10, Kraków',      'lat': 50.0647, 'lon': 19.9450},
        {'name': 'Oddział Wrocław',   'address': 'ul. Świdnicka 20, Wrocław',      'lat': 51.1079, 'lon': 17.0385},
    ],
    'piotr_wisniewski': [
        {'name': 'Centrum Gdańsk',    'address': 'ul. Długa 5, Gdańsk',            'lat': 54.3520, 'lon': 18.6466},
        {'name': 'Oddział Poznań',    'address': 'ul. Półwiejska 30, Poznań',      'lat': 52.4064, 'lon': 16.9252},
    ],
}

JOBS_PER_USER = 15
VEHICLES_PER_USER = 3

# Kolory dla poszczególnych typów pojazdów
VEHICLE_COLORS = {
    'Van #1':   (70,  130, 180),  # stalowy niebieski
    'Van #2':   (60,  179, 113),  # zielony
    'Truck #1': (205,  92,  92),  # czerwony
}


def generate_vehicle_photo(name):
    """Generuje prosty kolorowy obrazek z nazwą pojazdu używając Pillow."""
    color = VEHICLE_COLORS.get(name, (150, 150, 150))
    img = Image.new('RGB', (400, 200), color=color)
    draw = ImageDraw.Draw(img)

    # Napis z nazwą pojazdu na środku
    draw.text((200, 80),  name,          fill='white', anchor='mm')
    draw.text((200, 120), 'GeoPlanner',  fill='white', anchor='mm')

    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    filename = name.replace(' ', '_').replace('#', '') + '.jpg'
    return ContentFile(buffer.read(), name=filename)


class Command(BaseCommand):
    help = 'Wypełnia bazę danych testowymi danymi. Usuwa poprzednie dane testowe.'

    def handle(self, *args, **kwargs):
        self.stdout.write('Czyszczenie starych danych testowych...')
        User.objects.filter(username__in=[u['username'] for u in SEED_USERS]).delete()

        vehicle_types = list(VehicleType.objects.all())
        if not vehicle_types:
            self.stdout.write(self.style.ERROR('Brak VehicleType w bazie. Dodaj słowniki przez admin i spróbuj ponownie.'))
            return

        for user_data in SEED_USERS:
            user = User.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
            )
            self.stdout.write(f'  Tworzę użytkownika: {user.username}')

            # Depoty — dane zdefiniowane w DEPOTS dla danego użytkownika
            depots_data = DEPOTS[user.username]
            depots = []
            for d in depots_data:
                depot = Depot.objects.create(
                    user=user,
                    name=d['name'],
                    address=d['address'],
                    latitude=d['lat'],
                    longitude=d['lon'],
                )
                depots.append(depot)
            self.stdout.write(f'    → {len(depots)} depoty')

            # Joby — współrzędne ±0.1 od pierwszego depotu użytkownika,
            # miasto w adresie = miasto depotu (żeby adres pasował do punktu na mapie)
            base_lat = depots[0].latitude
            base_lon = depots[0].longitude
            base_city = depots[0].address.split(',')[-1].strip()
            for i in range(1, JOBS_PER_USER + 1):
                Job.objects.create(
                    user=user,
                    address=fake.street_address() + ', ' + base_city,
                    job_code=f'JOB-{user.username[:3].upper()}-{i:03d}',
                    latitude=round(base_lat + random.uniform(-0.1, 0.1), 6),
                    longitude=round(base_lon + random.uniform(-0.1, 0.1), 6),
                    service_time_minutes=random.choice([10, 15, 20, 30]),
                    demand=random.randint(1, 50),
                )
            self.stdout.write(f'    → {JOBS_PER_USER} jobów')

            # Pojazdy
            vehicle_names = ['Van #1', 'Van #2', 'Truck #1']
            for i in range(VEHICLES_PER_USER):
                vehicle = Vehicle(
                    user=user,
                    vehicle_type=random.choice(vehicle_types),
                    name=vehicle_names[i],
                    capacity=random.choice([50, 100, 150, 200]),
                    starting_time='08:00:00',
                    working_time_minutes=480,
                )
                vehicle.photo.save(
                    f'{vehicle_names[i].replace(" ", "_").replace("#", "")}.jpg',
                    generate_vehicle_photo(vehicle_names[i]),
                    save=True,
                )
            self.stdout.write(f'    → {VEHICLES_PER_USER} pojazdy (ze zdjęciami)')

        self.stdout.write(self.style.SUCCESS('\nGotowe! Użytkownicy testowi:'))
        for u in SEED_USERS:
            self.stdout.write(f'  login: {u["username"]}  hasło: {u["password"]}')
