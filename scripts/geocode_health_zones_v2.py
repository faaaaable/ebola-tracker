name: Géocodage zones de santé v2 (contraint par province)

on:
  workflow_dispatch:

jobs:
  geocode:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Lancer le géocodage v2
        run: python scripts/geocode_health_zones_v2.py
