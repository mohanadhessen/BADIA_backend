from fastapi import APIRouter, Depends , HTTPException , status 
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from database.session import get_db
from crud.admin import (
    admin_get_all_users,
    admin_get_user_by_email,
    get_users_plans_distribution,
    admin_get_all_requests,
    admin_get_all_review,
    admin_update_request_status,
    admin_delete_request,
    admin_delete_review,
    admin_set_review_publish_status,
    admin_update_user_data
)
from ...dependencies import require_admin 
from schemas.admin import StatusUpdate , ReviewPublishUpdate , AdminUserUpdateSchema
from r2_client import s3
from config import settings
from crud.request import get_request_by_id
from models.user_file import user_file
from schemas.plan import PlanUpdate, PlanResponse , PlanBase
from crud.plan import get_plan_by_id, update_plan , get_plan_by_name , delete_plan , create_plan

R2_BUCKET = settings.R2_BUCKET


router = APIRouter(
    prefix="",
    tags=["admin"],
    dependencies=[Depends(require_admin)]
)



@router.get("/users")
def get_all_users(
    page: int = 1,
    limit: int = 25,
    only_active: bool = False,
    db: Session = Depends(get_db)
):
    return admin_get_all_users(
        db=db,
        page=page,
        limit=limit,
        only_active=only_active
    )


@router.get("/users/plan-distribution")
def get_users_plan_distribution(db: Session = Depends(get_db)):
    return get_users_plans_distribution(db)





@router.patch("/users/{email}")
def update_user_data(
    email: str,
    payload: AdminUserUpdateSchema,
    db: Session = Depends(get_db)
):
    update_dict = payload.model_dump(exclude_unset=True)

    updated_user = admin_update_user_data(
        db=db,
        email=email,
        update_data=update_dict
    )

    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return updated_user

@router.get("/users/by-email")
def get_user_by_email(email: str, db: Session = Depends(get_db)):
    user = admin_get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user



@router.get("/reviews")
def get_all_reviews(
    page: int = 1,
    limit: int = 25,
    db: Session = Depends(get_db)
):
    return admin_get_all_review(
        db=db,
        page=page,
        limit=limit
    )


@router.get("/requests")
def get_all_requests(
    page: int = 1,
    limit: int = 25,
    db: Session = Depends(get_db)
):
    return admin_get_all_requests(
        db=db,
        page=page,
        limit=limit
    )


@router.patch("/requests/{request_id}/status")
def update_request_status(
    request_id: str,
    body: StatusUpdate,
    db: Session = Depends(get_db)
):
    allowed_statuses = {"pending", "approved", "rejected"}

    if body.status not in allowed_statuses:
        raise HTTPException(400, "Invalid status")

    updated_request = admin_update_request_status(
        db=db,
        request_id=request_id,
        status=body.status
    )

    if not updated_request:
        raise HTTPException(404, "Request not found")

    return updated_request


@router.delete("/requests/{request_id}")
def delete_request(
    request_id: str,
    db: Session = Depends(get_db)
):
    success = admin_delete_request(db=db, request_id=request_id)

    if not success:
        raise HTTPException(404, "Request not found")

    return {
        "message": "Request deleted successfully",
        "request_id": request_id
    }



@router.delete("/reviews/{review_id}")
def delete_review(
    review_id: int,
    db: Session = Depends(get_db)
):
    success = admin_delete_review(db=db, review_id=review_id)

    if not success:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return {"success": True, "review_id": review_id}





@router.patch("/reviews/{review_id}/publish")
def set_review_publish_status(
    review_id: int,
    body: ReviewPublishUpdate,
    db: Session = Depends(get_db)
):
    review = admin_set_review_publish_status(
        db=db,
        review_id=review_id,
        is_published=body.is_published
    )

    if not review:
        raise HTTPException(
            status_code=404,
            detail="Review not found"
        )

    return review






@router.get("/requests/{request_id}/files/{file_id}")
def download_request_file(request_id: int, file_id: str, db: Session = Depends(get_db)):
    request = get_request_by_id(db=db, request_id=request_id)

    if not request:
        raise HTTPException(404, "Request not found")

    db_file = db.query(user_file).filter(
        user_file.file_id == file_id,
        user_file.request_id == request_id
    ).first()

    if not db_file:
        raise HTTPException(404, "File not found")

    try:
        presigned_url = s3.generate_presigned_url(
            "get_object",
            Params={
                "Bucket": R2_BUCKET,
                "Key": db_file.file_key,
                "ResponseContentDisposition": f'attachment; filename="{db_file.filename}"',
            },
            ExpiresIn=300
        )
    except Exception as e:
        raise HTTPException(500, f"Could not generate download URL: {str(e)}")

    return JSONResponse({
        "url": presigned_url,
        "filename": db_file.filename
    })







def get_bucket_storage_usage(s3_client, bucket_name):
    paginator = s3_client.get_paginator("list_objects_v2")

    total_bytes = 0
    total_files = 0

    for page in paginator.paginate(Bucket=bucket_name):
        for obj in page.get("Contents", []):
            total_bytes += obj["Size"]
            total_files += 1

    total_gb = total_bytes / (1024 ** 3)

    return {
        "total_bytes": total_bytes,
        "total_gb": round(total_gb, 4),
        "total_files": total_files,
    }



@router.get("/storage/usage")
def get_storage_usage():
    paginator = s3.get_paginator("list_objects_v2")

    total_bytes = 0
    total_files = 0

    for page in paginator.paginate(Bucket=settings.R2_BUCKET):
        for obj in page.get("Contents", []):
            total_bytes += obj["Size"]
            total_files += 1

    total_gb = total_bytes / (1024 ** 3)

    FREE_TIER_GB = 10  

    return {
    "used_bytes": total_bytes,
    "used_kb": round(total_bytes / 1024, 2),
    "used_mb": round(total_bytes / (1024 ** 2), 4),
    "used_gb": round(total_bytes / (1024 ** 3), 6),
    "remaining_gb": round(max(FREE_TIER_GB - total_gb, 0), 6),
    "usage_percent": round((total_gb / FREE_TIER_GB) * 100, 6),
    "total_files": total_files,
    }




@router.post("/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
def create_new_plan(
    plan_data: PlanBase,
    db: Session = Depends(get_db),
):
    # prevent duplicate plan names
    existing_plan = get_plan_by_name(db, plan_data.name)
    
    if existing_plan:
        raise HTTPException(
            status_code=400,
            detail="Plan name already exists"
        )

    plan = create_plan(
        db=db,
        data=plan_data.model_dump()
    )

    return plan



@router.patch("/plans/{plan_id}", response_model=PlanResponse)
def edit_plan(
    plan_id: int,
    plan_data: PlanUpdate,
    db: Session = Depends(get_db),
):
    plan = get_plan_by_id(db, plan_id)

    if not plan:
        raise HTTPException(404, "Plan not found")

    if (
        plan_data.name and
        plan_data.name != plan.name and
        get_plan_by_name(db, plan_data.name)
    ):
        raise HTTPException(400, "Plan name already exists")

    return update_plan(
        db=db,
        plan=plan,
        data=plan_data.model_dump(exclude_unset=True)
    )

   
@router.delete("/plans/{plan_id}")
def delete_plan_by_id(  
    plan_id: int,
    db: Session = Depends(get_db)
    ):
    plan = get_plan_by_id(db, plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    
    delete_plan(db, plan)
    
    return {"message": "Plan deleted successfully"}

   