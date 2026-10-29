import json
import sqlite3
from typing import Any

from .config import settings
from .logger import logger


class CaseDB:
    """SQLite database for case management and evidence tracking"""
    
    def __init__(self):
        self.db_path = settings.data_dir / "cases.db"
        self.init_db()
    
    def init_db(self):
        """Initialize database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                target TEXT,
                description TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'open'
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER,
                module TEXT NOT NULL,
                input_data TEXT,
                result_json TEXT,
                risk_level TEXT DEFAULT 'info',
                tags TEXT,
                notes TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (case_id) REFERENCES cases (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                case_id INTEGER,
                url TEXT,
                method TEXT,
                module TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                response_code INTEGER,
                FOREIGN KEY (case_id) REFERENCES cases (id)
            )
        """)
        
        conn.commit()
        conn.close()
        logger.debug(f"Database initialized at {self.db_path}")
    
    def create_case(self, name: str, target: str | None = None, description: str | None = None) -> int:
        """Create a new investigation case"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO cases (name, target, description) VALUES (?, ?, ?)",
                (name, target, description)
            )
            case_id = cursor.lastrowid
            conn.commit()
            if case_id is None:  # pragma: no cover - INSERT always sets lastrowid
                raise RuntimeError("INSERT into cases did not return a rowid")
            logger.info(f"Created case '{name}' (ID: {case_id})")
            return case_id
        except sqlite3.IntegrityError:
            logger.error(f"Case '{name}' already exists")
            raise
        finally:
            conn.close()
    
    def list_cases(self) -> list[dict[str, Any]]:
        """List all cases"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cases ORDER BY created_at DESC")
        cases = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return cases
    
    def get_case(self, case_id: int) -> dict[str, Any] | None:
        """Get case by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cases WHERE id = ?", (case_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def add_finding(self, case_id: int, module: str, input_data: str, 
                   result: dict[str, Any], risk_level: str = "info", 
                   tags: list[str] | None = None, notes: str | None = None) -> int:
        """Add a finding to a case"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        tags_str = ",".join(tags) if tags else ""
        cursor.execute(
            """INSERT INTO findings (case_id, module, input_data, result_json, 
               risk_level, tags, notes) VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (case_id, module, input_data, json.dumps(result), risk_level, tags_str, notes)
        )
        finding_id = cursor.lastrowid
        conn.commit()
        if finding_id is None:  # pragma: no cover - INSERT always sets lastrowid
            raise RuntimeError("INSERT into findings did not return a rowid")
        conn.close()
        logger.debug(f"Added finding to case {case_id}")
        return finding_id
    
    def get_findings(self, case_id: int) -> list[dict[str, Any]]:
        """Get all findings for a case"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM findings WHERE case_id = ? ORDER BY timestamp DESC", (case_id,))
        findings = []
        for row in cursor.fetchall():
            finding = dict(row)
            finding['result'] = json.loads(finding['result_json'])
            if finding['tags']:
                finding['tags'] = finding['tags'].split(',')
            findings.append(finding)
        conn.close()
        return findings

db = CaseDB()
