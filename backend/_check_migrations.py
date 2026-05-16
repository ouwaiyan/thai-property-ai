import os
versions = os.listdir("alembic/versions")
print("Migration versions:", sorted([v for v in versions if v.endswith('.py')]))
