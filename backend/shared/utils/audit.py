from backend.database import SessionLocal
from backend.shared.models.audit_log import AuditLog

def log_action(user_id, action, entity, entity_id=None, description=""):
    db = SessionLocal()

    log = AuditLog(
        user_id=user_id,
        action=action,
        entity=entity,
        entity_id=entity_id,
        description=description
    )

    db.add(log)
    db.commit()
    db.close()