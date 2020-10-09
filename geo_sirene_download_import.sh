#! /bin/bash

# Script de téléchargement et chargement des données RPG dans postgresql

for CMD in wget unzip psql
do
  if [ "$(which $CMD)" = "" ]
  then
    echo "$CMD non installé"
    echo "sudo apt install wget unzip postgresql"
    exit
  fi
done

mkdir -p data
cd data

DB=$USER

wget -N http://files.data.gouv.fr/insee-sirene/StockUniteLegale_utf8.zip
wget -N http://data.cquest.org/geo_sirene/v2019/last/StockEtablissement_utf8_geo.csv.gz

# création de la table SIREN (entreprises)
psql $DB -c "create table siren_temp (`unzip -p StockUniteLegale_utf8.zip | head -n 1 | sed 's/,/ text,/g;s/$/ text/'`);"
unzip -p StockUniteLegale_utf8.zip | psql $DB -c "\copy siren_temp from stdin with (format csv, header true)"
# optimisation: clustering de la table sur SIREN
psql $DB -c "drop table if exists siren cascade; create table siren as (select * from siren_temp order by siren); drop table siren_temp;"
# création d'un index rapide (BRIN) sur SIREN
psql $DB -c "create index on siren using brin (siren);"

# création de la table des établissements
psql $DB -c "drop table if exists siret_temp; create table siret_temp (`zcat StockEtablissement_utf8_geo.csv.gz | head -n 1 | sed 's/,/ text,/g;s/$/ text/'`);"
zcat StockEtablissement_utf8_geo.csv.gz | psql $DB -c "\copy siret_temp from stdin with (format csv, header true)"
# optimisation: clustering de la table sur SIRET
psql $DB -c "drop table if exists siret cascade; create table siret as (select * from siret_temp order by siret); drop table siret_temp"
# création d'un index rapide (BRIN) sur SIREN et SIRET
psql $DB -c "create index on siret using brin (siren); create index on siret using brin (siret);"

# ajout colonne géo + index
psql $DB -c "
alter table siret add geom geometry;
update siret set geom = st_makepoint(lon::numeric, lat::numeric);
create index on siret using gist(geom);
"
