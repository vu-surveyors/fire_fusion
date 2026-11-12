import os
from pathlib import Path
import duckdb
from sqlmodel import SQLModel, Session, create_engine

# Database path in apps/api/data
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DB_PATH = Path(os.getenv("DUCKDB_PATH", str(BASE_DIR / "data" / "fire_fusion.duckdb")))
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"duckdb:///{DB_PATH.as_posix()}"

engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"read_only": True}
)

def init_db():
    """Create all SQLModel tables in DuckDB."""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Yield a SQLModel database session."""
    with Session(engine) as session:
        yield session

def get_duckdb_conn(read_only: bool = True):
    """Return a direct raw duckdb connection for ultra-fast columnar operations.
    
    Uses read_only=True by default for API queries.
    DuckDB 2.0 allows multiple concurrent read-only connections.
    """
    return duckdb.connect(str(DB_PATH), read_only=read_only)

