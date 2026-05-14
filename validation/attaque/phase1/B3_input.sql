SELECT a.toponyme, a.categorie,
       (SELECT count(*) FROM equipement_de_transport e
        WHERE e.nature = 'Tour de contrôle aérien'
          AND ST_DWithin(e.geometrie, a.geometrie, 1000)) AS tours_proches
FROM aerodrome a
WHERE a.categorie IN ('Internationale', 'Nationale');
