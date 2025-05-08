from datetime import datetime
from sqlalchemy.orm import Session
from app.sql_app.dbmodels import job_saves 

class JobSaveService:
    def __init__(self, db: Session):
        self.db = db
        pass

    def save_job_state(self, key: str, run_timestamp: datetime, is_success: bool=False):
        # obj = job_saves.JobSaves(
        #     job_key=key,
        #     last_run=last_run,
        #     last_successful_run=last_successful_run
        # )
        job_save = self.db.get(job_saves.JobSaves, key)

        last_run = run_timestamp
        last_successful_run = run_timestamp if is_success else None

        if(job_save is None):
            job_save = job_saves.JobSaves(
                job_key=key,
                last_run=last_run,
                last_successful_run=last_successful_run
            )
        else:
            job_save.last_run = last_run
            job_save.last_successful_run = run_timestamp if is_success else job_save.last_successful_run
           
        self.db.add(job_save)
        self.db.commit()
        self.db.refresh(job_save)
        return job_save
    
    def get_job_state(self, key: str):
        job_save = self.db.get(job_saves.JobSaves, key)
        if(job_save is None):
            job_save = job_saves.JobSaves(
                job_key=key,
                last_run=None,
                last_successful_run=None
            )
        return job_save