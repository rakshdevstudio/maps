import sys
import os
sys.path.append(os.path.dirname(__file__))

from app.database import SessionLocal
from app.ai.orchestration.daily_briefing_engine import run_daily_orchestration

db = SessionLocal()
try:
    run_daily_orchestration(db)
except Exception as e:
    import traceback
    traceback.print_exc()
finally:
    db.close()
