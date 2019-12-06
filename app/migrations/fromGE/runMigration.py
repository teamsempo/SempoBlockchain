import os
import sys

dirname = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(dirname, "..", "..", "..")))
sys.path.append(os.path.abspath(os.path.join(dirname, "..", "..")))

from migrations.fromGE.RDSMigrate import RDSMigrate
from server import create_app, db, bt



if __name__ == "__main__":
    app = create_app()
    ctx = app.app_context()
    ctx.push()

    rds = RDSMigrate()
    rds.migrate()
