import os
import sys

dirname = os.path.dirname(__file__)
sys.path.append(os.path.abspath(os.path.join(dirname, "..", "..", "..")))
sys.path.append(os.path.abspath(os.path.join(dirname, "..", "..")))

from migrations.fromGE.rds_migrate import RDSMigrate
from server import create_app, db, bt



if __name__ == "__main__":
    app = create_app()
    ctx = app.app_context()
    ctx.push()

    rds = RDSMigrate(sempo_token_id=1)
    rds.migrate()
