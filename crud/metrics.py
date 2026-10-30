from sqlalchemy.ext.asyncio import AsyncSession 
from sqlalchemy import func , select
from datetime import datetime
from models.email_metric import EmailMetric
from models.user_file import UserFile



async def create_email_log(db: AsyncSession, recipient: str, subject: str):
    new_log = EmailMetric(recipient=recipient, subject=subject)
    db.add(new_log)
    await db.commit()
    await db.refresh(new_log)
    return new_log


# todo add the metrics get crud later

# async def get_emails_metric(db:AsyncSession):
    
    


# async def get_files_metric(db: AsyncSession):
    