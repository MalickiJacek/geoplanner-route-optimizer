# Docker – GeoPlanner (notatki PL)

## Jak to działa

Projekt składa się z 3 kontenerów zarządzanych przez `docker-compose.yml`:

```
┌─────────────────────────────────────────────┐
│              docker-compose.yml             │
│                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │    db    │  │ backend  │  │ frontend │  │
│  │ postgres │  │  django  │  │   vite   │  │
│  │  :5432   │  │  :8000   │  │  :5173   │  │
│  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────┘
```

- `db` startuje pierwszy (backend czeka na jego healthcheck)
- `backend` startuje po db
- `frontend` startuje po backend

Dane PostgreSQL są przechowywane w Docker volume `postgres_data` — przeżywają restarty i `docker compose down`. Usuwa je tylko `docker compose down -v`.

---

## Volume mounts — kluczowa zasada

W `docker-compose.yml` mamy:

```yaml
backend:
  volumes:
    - ./backend:/app        # Twój kod lokalny = kod w kontenerze

frontend:
  volumes:
    - ./frontend:/app       # Twój kod lokalny = kod w kontenerze
    - /app/node_modules     # wyjątek: node_modules zostają z obrazu
```

**Co to oznacza w praktyce:** katalog na Twoim dysku i katalog w kontenerze to TO SAMO miejsce. Edytujesz plik w VS Code → kontener widzi zmianę natychmiast.

---

## Czy po zmianie kodu trzeba restartować?

| Co zmieniłeś | Restart potrzebny? | Co zrobić |
|---|---|---|
| Plik `.py` (widok, serializer, model itp.) | NIE | Django auto-reloader wykrywa zmianę automatycznie |
| Plik `.jsx` / `.js` / `.css` | NIE | Vite HMR odświeża przeglądarkę automatycznie |
| `requirements.txt` | TAK | `docker compose up -d --build` |
| `package.json` | TAK | `docker compose up -d --build` |
| `settings.py` | NIE (auto-reload) | Ewentualnie restart backendu jeśli coś się nie odświeżyło |
| `.env` | TAK | `docker compose up -d` (bez --build) |
| `models.py` (nowe migracje) | NIE | Tylko uruchom `migrate` (patrz niżej) |

---

## Migracje

Backend przy starcie sam uruchamia `python manage.py migrate` (patrz `command` w `docker-compose.yml`), więc na czystej bazie od razu powstają tabele i słowniki (typy tras, pojazdów, statusy).

### Nowe migracje po zmianie modeli

```bash
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
```

Lub przez GUI Docker Desktop: Containers → backend → Exec → wpisz komendę.

---

## Komendy — codzienna praca

### Start i stop

```bash
docker compose up -d              # start wszystkich kontenerów w tle
docker compose down               # stop (dane w bazie zostają)
docker compose down -v            # stop + USUWA dane bazy (ostrożnie!)
```

### Przebudowanie po zmianie requirements.txt lub package.json

```bash
docker compose up -d --build
```

### Logi

```bash
docker compose logs backend       # logi Django
docker compose logs frontend      # logi Vite
docker compose logs db            # logi PostgreSQL
docker compose logs -f backend    # logi na żywo (follow)
```

### Uruchomienie komendy w kontenerze

```bash
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py shell
docker compose exec db psql -U geoplanner -d geoplanner
```

---

## GUI Docker Desktop — odpowiedniki

| Chcesz | GUI | Komenda |
|---|---|---|
| Uruchomić projekt | Containers → geoplanner-route-optimizer → Play | `docker compose up -d` |
| Zatrzymać projekt | Containers → geoplanner-route-optimizer → Stop | `docker compose down` |
| Zobaczyć logi | Containers → backend/frontend/db → Logs | `docker compose logs <serwis>` |
| Uruchomić komendę | Containers → backend → Exec | `docker compose exec backend <komenda>` |
| Sprawdzić stan | Containers (zielona ikona = działa) | `docker compose ps` |
| Usunąć wszystko z danymi | Volumes → postgres_data → Delete | `docker compose down -v` |

---

## Konfiguracja — gdzie co jest

| Plik | Co zawiera |
|---|---|
| `docker-compose.yml` | Definicja serwisów, portów, volumenów |
| `.env` (root, kopia `.env.example`) | Wszystkie zmienne: Django, baza danych, limit czasu solvera |
| `frontend/.env` (opcjonalnie) | `VITE_API_URL` – adres backendu dla przeglądarki |
| `backend/Dockerfile` | Jak budowany jest obraz Django |
| `frontend/Dockerfile` | Jak budowany jest obraz Vite/React |

---

## Backup i przywracanie bazy

### Backup

```bash
docker compose exec -T db pg_dump -U geoplanner geoplanner > geoplanner_backup.sql
```

### Przywracanie do kontenera

```bash
docker compose exec backend python manage.py migrate
docker compose exec -T db psql -U geoplanner -d geoplanner < geoplanner_backup.sql
```

---

## Uwagi środowiskowe

W Git Bash `docker` może nie być w PATH. Dodaj do `~/.bashrc`:

```bash
export PATH="$PATH:/c/Program Files/Docker/Docker/resources/bin"
```

Lub korzystaj z Docker Desktop GUI albo PowerShell gdzie PATH jest ustawiony poprawnie.
