from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models import Alert

router = APIRouter(prefix="/stats", tags=["stats"])

@router.get("/summary")
def get_stats(db: Session = Depends(get_db)):
    total_alerts = db.query(Alert).count()
    high_sev = db.query(Alert).filter(Alert.severity == "high").count()
    medium_sev = db.query(Alert).filter(Alert.severity == "medium").count()
    low_sev = db.query(Alert).filter(Alert.severity == "low").count()
    
    return {
        "total_alerts": total_alerts,
        "severity_breakdown": {
            "high": high_sev,
            "medium": medium_sev,
            "low": low_sev
        }
    }
