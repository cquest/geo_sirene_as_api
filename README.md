# Micro-API geo_sirene

Ce projet implémente une API minimale pour requêter la version géocodée de la base SIRENE de l'INSEE stockées dans une base locale postgresql/postgis.


## Installation

Ce projet est écrit en python 3 qui doit donc être installé. Les modules utilisés peuvent être installés avec:

`pip3 install -r requirements.txt`


## Chargement des données

Téléchargement et import des données :

`./geo_sirene_download_import.sh`


## Lancement du serveur

`gunicorn geo_sirene:app -b 0.0.0.0:8888`


## Paramètres reconnus par l'API

Codes SIREN ou SIRET:
- SIREN (entreprise): http://api.cquest.org/sirene?siren=377607825
- SIRET (établissement): http://api.cquest.org/sirene?siret=37760782500017


Sélection par proximité géographique:
- distance de 100m: http://api.cquest.org/sirene?lat=47.86&lon=3.40&dist=1000
- distance par défaut de 500m: http://api.cquest.org/sirene?lat=47.86&lon=3.40
- recherche par bounding box: http://api.cquest.org/sirene?bbox=2.3500,48.8500,2.3501,48.8501 (xmin,ymin,xmax,ymax)

Filtrage possible par:
- Code APE (Restaurants): http://api.cquest.org/sirene?lat=47.86&lon=3.40&dist=1000&apet=56.10

Le résultat est au format GeoJSON.

## Exemple d'utilisation

Carte uMap des restaurants, boulangeries, débits de boissons: https://umap.openstreetmap.fr/fr/map/demo-apicquestorgsirene_509001#17/48.80908/2.47509
