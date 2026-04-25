# Instructor Guide — Opération Manticore V2

## 1. Pré-cours checklist

- [ ] Docker stack fonctionnel (`docker compose up -d`)
- [ ] Gold Dumps générés pour les 10 EPCIs (`python scripts/admin_generate_gold_dumps.py --all`)
- [ ] CIFS store monté (`/media/stores/cifs/store-DAI/...`)
- [ ] Slides Marp buildées (`npx @marp-team/marp-cli slides/theorie_bdd_nosql.md -o slides/output.html`)
- [ ] Neo4j heap adapté aux laptops (512M si < 8GB RAM)

## 2. Assignation groupes × EPCI × rôles

| Groupe | EPCI | Agent 1 (Attaque) | Agent 2 (Défense) | Agent 3 (Ravitaillement) | Agent 4 (Énergie) |
|--------|------|-------------------|-------------------|--------------------------|-------------------|
| 1 | Brest Métropole | A1 | D1 | R1 | E1 |
| 2 | Le Havre Seine Métropole | A2 | D2 | R2 | E2 |
| 3 | CU de Dunkerque | A3 | D3 | R3 | E3 |
| 4 | CA du Cotentin | A4 | D4 | R4 | E4 |
| 5 | Grenoble-Alpes-Métropole | A5 | D5 | R5 | E5 |
| 6 | Eurométropole de Strasbourg | A6 | D6 | R6 | E6 |
| 7 | Métropole Européenne de Lille | A7 | D7 | R7 | E7 |
| 8 | CA du Pays Basque | A8 | D8 | R8 | E8 |
| 9 | Métropole Rouen Normandie | A9 | D9 | R9 | E9 |
| 10 | Bordeaux Métropole | A10 | D10 | R10 | E10 |

## 3. Points de blocage fréquents

- **Mémoire Neo4j** : réduire heap dans `docker-compose.yml` si < 8GB RAM
- **SRID** : BDTOPO = Lambert-93 (EPSG:2154). Les coords GPS sont en 4326 → `ST_Transform`
- **Cypher MERGE** : sans index, très lent. Créer les index avant la migration
- **r2gg absent** : Gold Dumps doivent être pré-générés par l'instructeur
- **importance colonne** : VARCHAR dans BDTOPO, caster en INTEGER pour les filtres numériques

## 4. Centrales nucléaires (custom POIs)

Injectées automatiquement par `00_setup.py` depuis les coords approximatives :

| Centrale | Coords | EPCI concerné |
|----------|--------|---------------|
| Gravelines | (2.14, 51.0) | CU de Dunkerque |
| Flamanville | (-1.85, 49.55) | CA du Cotentin |
| Cattenom | (6.25, 49.42) | CA du Pays Basque (proche) |
| Civaux | (0.65, 46.45) | Bordeaux Métropole (proche) |

Table : `mission_custom_pois` (id, nom, type, puissance_mw, geometrie)

## 5. Solutions des exercices

Les scripts `01` à `04` sont les corrigés complets. Pour distribuer aux étudiants, vider les parties marquées TODO ou fournir les énoncés dans `mission/`.
