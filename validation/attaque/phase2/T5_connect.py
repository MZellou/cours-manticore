from neo4j import GraphDatabase
d = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'manticore2026'))
s = d.session()
r = s.run('RETURN 1 AS test')
print([dict(x) for x in r])
s.close()
d.close()
