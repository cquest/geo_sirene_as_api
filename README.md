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

Sélection par proximité géographique:
- distance de 100m: http://api.cquest.org/sirene?lat=47.86&lon=3.40&dist=1000
- distance par défaut de 500m: http://api.cquest.org/sirene?lat=47.86&lon=3.40


Filtrage par:
- Code APE (Restaurants): http://api.cquest.org/sirene?lat=47.86&lon=3.40&dist=1000&apet=56.10

Le résultat est au format GeoJSON.
