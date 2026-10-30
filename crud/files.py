from models.user_file import UserFile
from sqlalchemy import   select
from sqlalchemy.ext.asyncio import AsyncSession 
from r2_client import s3
from config import settings
import asyncio

async def get_file_by_id (db: AsyncSession ,file_id: str ) :
    result = await db.execute(select(UserFile).where(UserFile.file_id == file_id))
    return result.scalar_one_or_none()


async def create_file(db: AsyncSession,request_id: int,file_key: str,filename: str,content_type: str,size: int,):
    new_file = UserFile(
        request_id=request_id,
        file_key=file_key,
        filename=filename,
        content_type=content_type,
        size=size,
    )
    db.add(new_file)
    await db.commit()
    await db.refresh(new_file)
    return new_file





async def delete_file(db: AsyncSession, file_id: str) -> bool:
    file = get_file_by_id(db,file_id)
    if not file:
        raise ValueError("File not found")
    await db.delete(file)
    await db.commit()
    return True






async def create_s3_upload_url(db: AsyncSession,file_id: str,file_size: int,expires_in: int = 300,content_type: str = "application/pdf",) -> dict:


    key = f"uploads/{file_id}"

    url = await asyncio.to_thread(s3.generate_presigned_url,"put_object",Params={"Bucket": settings.R2_BUCKET,"Key": key,"ContentType": content_type,"ContentLength": file_size,},ExpiresIn=expires_in,)

    return {"url": url,"key": key,"headers": {"Co7ntent-Type": content_type},
    }