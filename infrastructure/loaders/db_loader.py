import logging
import sqlite3
from pathlib import Path
from domain.errors import DomainError
from domain.interfaces import IDataLoader

logger = logging.getLogger(__name__)

class SqliteLoaderError(DomainError): pass

class SqliteLoader(IDataLoader):
    def load(self, source: str, table: str = None, **kwargs) -> list[dict]:
        logger.debug(f"SqliteLoader.load: {source}")
        path = Path(source)
        if not path.exists() or path.suffix.lower() not in (".db", ".sqlite", ".sqlite3"):
            raise SqliteLoaderError(f"Невалидная БД: {source}")
        conn = sqlite3.connect(str(path))
        try:
            if not table:
                tables = [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
                table = next((t for t in tables if conn.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] > 0), None)
                if not table: raise SqliteLoaderError("Нет непустых таблиц")
            cur = conn.execute(f'SELECT * FROM "{table}"')
            return [dict(zip([d[0] for d in cur.description], r)) for r in cur.fetchall()]
        except sqlite3.OperationalError as e:
            raise SqliteLoaderError(f"SQL ошибка: {e}")
        finally:
            conn.close()