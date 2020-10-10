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
psql $DB -c "drop table if exists siren; create table siren (`unzip -p StockUniteLegale_utf8.zip | head -n 1 | sed 's/,/ text,/g;s/$/ text/'`);"
unzip -p StockUniteLegale_utf8.zip | psql $DB -c "\copy siren from stdin with (format csv, header true)"
psql $DB -c "create index on siren (siren);" &
psql $DB -c "create index on siren (activiteprincipaleunitelegale);" &

# création de la table SIRET des établissements
psql $DB -c "drop table if exists siret_temp; create table siret_temp (`zcat StockEtablissement_utf8_geo.csv.gz | head -n 1 | sed 's/,/ text,/g;s/$/ text/'`);"
psql $DB -c "
alter table siret_temp alter longitude type float USING longitude::double precision;
alter table siret_temp alter latitude type float USING longitude::double precision;
alter table siret_temp alter geo_score type float USING longitude::double precision;
"

zcat StockEtablissement_utf8_geo.csv.gz | psql $DB -c "\copy siret_temp from stdin with (format csv, header true)"
# ajout colonne geo
psql $DB -c "
ALTER TABLE siret_temp ADD geom geometry;
UPDATE siret_temp SET geom = ST_makepoint(longitude::numeric, latitude::numeric);
"

# optimisation: clustering géo de la table
psql $DB -c "drop table if exists siret; create table siret as (select * from siret_temp order by geom); drop table siret_temp"
# création des index
psql $DB -c "create index on siret (siren);" &
psql $DB -c "create index on siret (siret);" &
psql $DB -c "create index on siret (activiteprincipaleetablissement);" &
psql $DB -c "create index on siret using gist(geom);" &
psql $DB -c "create index on siret using gist(geom) where etatadministratifetablissement='A';" &
