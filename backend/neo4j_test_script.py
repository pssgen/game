from neo4j import GraphDatabase

uri = "bolt://127.0.0.1:7687"
user = "neo4j"
password = "00900p009"

driver = GraphDatabase.driver(uri, auth=(user, password))

with driver.session() as session:
    # Create test nodes
    for i in range(1, 4):
        session.run("CREATE (n:TestNode {name: $name})", {"name": f"Node-{i}"})
    print("✓ Created 3 TestNode nodes.")
    # Query test nodes
    result = session.run("MATCH (n:TestNode) RETURN n.name AS name")
    print("TestNode names in database:")
    for record in result:
        print("-", record["name"])

driver.close()
print("✓ Neo4j test complete.")
