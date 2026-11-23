# Changelog

Each release maps to one of the provided ACEest desktop versions (see `legacy/`) and is tagged `v<version>` in Git and `<dockerhub-user>/aceest-fitness:<version>` on Docker Hub.

| Version | Desktop source | Flask feature added |
|---|---|---|
| 1.0 | Aceestver-1.0.py | Programs API (Fat Loss / Muscle Gain / Beginner workout + diet plans), health & version endpoints |
| 1.1 | Aceestver-1.1.py | Client profiles with calorie estimation (weight x program factor) |
| 1.1.2 | Aceestver1.1.2.py | CSV export of clients |
| 2.0.1 | Aceestver2.0.1.py | SQLite persistence and weekly adherence tracking |
| 2.1.2 | Aceestver-2.1.2.py | Bug fix: JSON booleans no longer accepted as adherence values |
| 2.2.1 | Aceestver-2.2.1.py | Progress chart data endpoint (replaces matplotlib chart) |
| 2.2.4 | Aceestver-2.2.4.py | Workout log, body metrics, BMI with category |
| 3.0.1 | Aceestver-3.0.1.py | Stable platform release: Docker, Jenkins, SonarQube and Kubernetes delivery |
| 3.1.2 | Aceestver-3.1.2.py | Login (hashed passwords), AI-style program generator, client report |
