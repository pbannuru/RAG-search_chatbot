from datetime import datetime, timedelta, timezone
from app.sql_app.database import DbDepends
from app.sql_app.dbmodels.core_audit_log import CoreAuditLog
from app.config import app_config

audit_log_retention_configs = app_config.AppConfig.get_sectionwise_configs(
    "audit_log_retention"
)


def delete_old_logs():
    threshold_date = datetime.now(timezone.utc) - timedelta(
        days=int(audit_log_retention_configs["num_of_days"])
    )

    with DbDepends() as db:
        db.query(CoreAuditLog).filter(CoreAuditLog.timestamp < threshold_date).delete(
            synchronize_session=False
        )
        db.commit()
        print(f"Deleted logs older than {threshold_date}.")


if __name__ == "__main__":
    delete_old_logs()
