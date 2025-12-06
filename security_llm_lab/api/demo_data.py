from datetime import datetime, timedelta
import random
from .elastic import index_log, create_index
from .database import SessionLocal
from .models import Alert

async def seed_demo_data():
    """Seeds Elasticsearch with dummy logs and Postgres with dummy alerts."""
    
    # 1. Seed Elastic Logs
    index_name = "winlogbeat-demo"
    await create_index(index_name)
    
    event_actions = ["Logon", "Process Create", "File Create", "Network Connection", "Logon Failed"]
    hosts = ["WORKSTATION-01", "DC-01", "SERVER-02"]
    users = ["admin", "john.doe", "jane.smith", "system"]
    
    print("Seeding Elastic Logs...")
    for i in range(50):
        # Create logs spread over last 24 hours
        time_offset = random.randint(0, 1440)
        timestamp = (datetime.utcnow() - timedelta(minutes=time_offset)).isoformat()
        
        log = {
            "timestamp": timestamp,
            "event_id": str(random.choice([4624, 4625, 1, 3])),
            "event_action": random.choice(event_actions),
            "host": {"name": random.choice(hosts)},
            "user": {"name": random.choice(users)},
            "message": "Sample log message for demo purposes."
        }
        await index_log(index_name, log)
        
    # 2. Seed Postgres Alerts
    db = SessionLocal()
    if db.query(Alert).count() == 0:
        print("Seeding Alerts...")
        alerts = [
            Alert(
                title="Brute Force Attempt detected",
                severity="high",
                source="Rule Engine",
                description="Multiple failed login attempts detected on DC-01.",
                status="new",
                raw_data={"count": 50, "user": "admin"}
            ),
             Alert(
                title="Suspicious Process Execution",
                severity="medium",
                source="ML Model",
                description="powershell.exe executed with encoded command.",
                status="investigating",
                raw_data={"cmd": "powershell -enc ..."}
            ),
              Alert(
                title="New User Created",
                severity="low",
                source="Winlogbeat",
                description="User 'test_user' was created.",
                status="resolved",
                raw_data={"user": "test_user"}
            )
        ]
        db.add_all(alerts)
        db.commit()
    db.close()
    print("Demo Data Seeded.")
