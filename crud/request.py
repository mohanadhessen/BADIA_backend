from sqlalchemy.ext.asyncio import AsyncSession 
from models.request import Request
from sqlalchemy import select 
from crud.user import get_user_by_email
import uuid
import asyncio

async def get_existing_request(db: AsyncSession, user_id: int, service_type: str) -> Request | None:
    result = await db.execute(select(Request).where(Request.user_id == user_id , Request.service_type == service_type,))
    return result.scalar_one_or_none()


async def create_request(db: AsyncSession, user_id: int, service_type: str) -> Request:
    new_request = Request(
        user_id=user_id,
        request_id=str(uuid.uuid4()),
        service_type=service_type,
        status="pending"
    )
    db.add(new_request)
    await db.commit()
    await db.refresh(new_request)
    return new_request

async def get_request_by_id(db: AsyncSession, request_id: str) -> Request | None:
    result = await db.execute(select(Request).where(Request.id == request_id))
    return result.scalar_one_or_none()



async def get_user_requests(db: AsyncSession, user_id: int)->list[Request]:
    result = await db.execute(select(Request).where(Request.user_id == user_id))
    return list(result.scalars().all())
  


async def get_requests_by_user_email(db: AsyncSession, email: str)->list[Request]:
    user = await  get_user_by_email(db,email)
    if not user:
        raise ValueError("User not found")
    result = await db.execute(select(Request).where(Request.user_id == user.id))
    return list(result.scalars().all())



async def update_request_status(  db: AsyncSession, request_id: str, new_status: str) -> Request | None:
    request = await get_request_by_id(db, request_id)
    if not request:
        raise ValueError("request not found")
    request.status = new_status
    await db.commit()
    await db.refresh(request)
    return request






async def delete_s3_file(s3, bucket: str, key: str):  
    if not key:
        return  
    await asyncio.to_thread(
    delete_s3_file,s3,bucket, key,)



async def delete_request( db: AsyncSession,request_id: str,s3,bucket: str):
    request = await get_request_by_id(db, request_id)
    if not request:
        raise ValueError("request not found")

    file_keys = [f.file_key for f in request.files if f.file_key]

    for key in file_keys:
        await delete_s3_file(s3=s3,bucket=bucket,key=key)

    await db.delete(request)
    await db.commit()


    return {"request_id": request_id,  "deleted_files": len(file_keys)}



