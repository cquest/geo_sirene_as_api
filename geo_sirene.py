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

        where = ''
        where2 = b''

        siret = req.params.get('siret', None)
        if siret and len(siret) == 14:
            where = cur.mogrify(' AND siret = %s ', (siret,))

        siren = req.params.get('siren', None)
        if siren and len(siren) == 9:
            where = cur.mogrify(' AND siren = %s ', (siren,))

        ape = req.params.get('ape', None)
        if ape:
            where2 = where2 + cur.mogrify(
                ' AND activiteprincipaleetablissement LIKE %s ', (ape+'%',))

        lat = req.params.get('lat', None)
        lon = req.params.get('lon', None)
        dist = min(int(req.params.get('dist', 500)), 1000)

        if lat and lon:  # recherche géographique
            query = cur.mogrify("""
select json_build_object('source', %s, 'derniere_maj', %s, 'licence', %s,
    'nb_resultats', count(r),
    'type','Featurecollection',
    'features', case when count(*)=0 then array[]::json[] else array_agg(json_build_object('type','Feature',
                                            'properties',json_strip_nulls(row_to_json(r)),
                                            'geometry',st_asgeojson(geom,6,0)::json)) end )::text
from (select coalesce(denominationusuelleetablissement,enseigne1etablissement, denominationunitelegale, denominationusuelle1unitelegale) as name, * from siret natural join siren
where st_buffer(st_setsrid(st_makepoint(%s, %s),4326)::geography, %s)::geometry && geom
    AND ST_DWithin(st_setsrid(st_makepoint(%s, %s),4326)::geography, geom::geography, %s)
    AND etatadministratifetablissement='A'
""", (SOURCE, DERNIER_MILLESIME, LICENCE, lon, lat, dist, lon, lat, dist)) + where2 + b') r'
        else:
            query = None

        if query or where != '':
            if not query:
                query = cur.mogrify("""
select json_build_object('source', %s, 'derniere_maj', %s, 'licence', %s,
    'nb_resultats', count(r),
    'resultats',array_to_json(array_agg(r)))::text
from (select coalesce(denominationusuelleetablissement,enseigne1etablissement, denominationunitelegale, denominationusuelle1unitelegale) as name, * from siret natural join siren
        where etatadministratifetablissement='A' """ + where.decode('utf8') + where2.decode('utf8') + """ ) r
""", (SOURCE, DERNIER_MILLESIME, LICENCE))

            print(query.decode())
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
