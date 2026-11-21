# Legacy prototype (2024) – plain HTML + JavaScript

🇵🇱 Pierwsza wersja projektu, zanim powstał GeoPlanner (Django + React). Zachowana jako punkt odniesienia.
🇬🇧 The first version of the project, before GeoPlanner (Django + React). Kept for reference.

| Page | What it did |
|---|---|
| `Geocode.html` | batch import of addresses from a `.txt` file, geocoding via Nominatim, markers on a Leaflet map |
| `TSP.html` | shortest route through imported points – **brute-force** search, route drawn on the map |
| `VRP.html` | like TSP, but split between vehicles with capacity and working time |
| `JMPage.html`, `index.html` | landing pages |

**Why it was rebuilt** – no users (everyone saw the same data), data lost on page refresh, no route history or authentication, and brute force became unusable above ~10 points (10 points = 3.6 million permutations). GeoPlanner replaced it with a REST API, JWT, PostgreSQL and Google OR-Tools.

Open any `.html` file directly in a browser. The original sample input files are not included.
