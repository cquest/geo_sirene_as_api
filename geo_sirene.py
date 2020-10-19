#! /usr/bin/python3

# modules additionnels
import falcon
import psycopg2

SOURCE = 'SIRENE / INSEE'
DERNIER_MILLESIME = '2020-10-01'
LICENCE = 'Licence Ouverte 2.0'

db = psycopg2.connect("")  # connexion à la base PG locale

class geo_sirene(object):
    def getSIRET(self, req, resp):
        cur = db.cursor()

        where = b''
        where2 = b''
        query = None

        siret = req.params.get('siret', None)
        if siret and len(siret) == 14:
            where = cur.mogrify(' AND siret = %s ', (siret,))

        siren = req.params.get('siren', None)
        if siren and len(siren) == 9:
            where = cur.mogrify(' AND siren.siren = %s ', (siren,))

        ape = req.params.get('ape', None)
        if ape:
            where2 = where2 + cur.mogrify( ' AND activiteprincipaleetablissement LIKE %s ', (ape+'%',))

        # recherche dans une bbox (xmin, ymin, xmax, ymax)
        bbox = req.params.get('bbox', None)
        if bbox:
            box = bbox.split(',')
            box2d = "ST_GeomFromText('LINESTRING(%f %f,%f %f)')" % (float(box[0]), float(box[1]), float(box[2]), float(box[3]))
            where = where + cur.mogrify(' AND geom && '+box2d)
        else:
            # recherche par centre/rayon géo (lat/lon/dist)
            lat = req.params.get('lat', None)
            lon = req.params.get('lon', None)
            dist = min(int(req.params.get('dist', 500)), 1000)
            if lat and lon:
                where = where + cur.mogrify("""
        AND st_buffer(st_setsrid(st_makepoint(%s, %s),4326)::geography, %s)::geometry && geom
        AND ST_DWithin(st_setsrid(st_makepoint(%s, %s),4326)::geography, geom::geography, %s)""",
                            (lon, lat, dist, lon, lat, dist))

        if where != '':
            query = cur.mogrify("""
select json_build_object('source', %s, 'derniere_maj', %s, 'licence', %s,
    'nb_resultats', count(r),
    'type','Featurecollection',
    'features', case when count(*)=0 then array[]::json[] else array_agg(json_build_object('type','Feature',
        'properties',json_strip_nulls(row_to_json(r)),
        'geometry',st_asgeojson(geom,6,0)::json)) end )::text
from (select coalesce(denominationusuelleetablissement,enseigne1etablissement, denominationunitelegale, denominationusuelle1unitelegale) as name, * from siret join siren on (siret.siren=siren.siren)
        where etatadministratifetablissement='A' """, (SOURCE, DERNIER_MILLESIME, LICENCE)) + where + where2 + b" ) r"

            cur.execute(query)
            out = cur.fetchone()

            resp.status = falcon.HTTP_200
            resp.set_header('X-Powered-By', 'geo_sirene_as_api')
            resp.set_header('Access-Control-Allow-Origin', '*')
            resp.set_header("Access-Control-Expose-Headers",
                            "Access-Control-Allow-Origin")
            resp.set_header('Access-Control-Allow-Headers',
                            'Origin, X-Requested-With, Content-Type, Accept')
            resp.set_header('X-Robots-Tag', 'noindex, nofollow')
            resp.body = out[0]
        else:
            resp.status = falcon.HTTP_413
            resp.body = '{"erreur": "aucun critère de recherche indiqué"}'


    def on_get(self, req, resp):
        self.getSIRET(req, resp)

# instance WSGI et route vers notre API
app = falcon.API()
app.add_route('/sirene', geo_sirene())
