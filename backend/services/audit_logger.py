import logging
import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from database import AuditLog, SessionLocal

logger = logging.getLogger("AuditLogger")

class AuditLogger:
    """
    Logs multi-agent system events to both a flat file and a MySQL database.
    """
    def log_event(self, action: str, session_id: str = None, user_id: str = None,
                  workflow_id: str = None, tool_name: str = None,
                  payload: dict = None, result: dict = None):
        
        # 1. Structured File Logging
        event_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "session_id": session_id,
            "user_id": user_id,
            "workflow_id": workflow_id,
            "tool_name": tool_name,
            "payload": payload,
            "result": result
        }
        logger.info(f"[AUDIT] {json.dumps(event_data)}")

        # 2. Database Logging (Async-compatible: create own session)
        try:
            with SessionLocal() as db:
                audit_entry = AuditLog(
                    user_id=user_id,
                    session_id=session_id,
                    workflow_id=workflow_id,
                    action=action,
                    tool_name=tool_name,
                    payload=payload,
                    result=result
                )
                db.add(audit_entry)
                db.commit()
        except Exception as e:
            logger.error(f"Failed to write to audit_logs table: {e}")

audit_logger = AuditLogger()
