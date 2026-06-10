from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
from database.session import get_db
from api.dependencies import require_admin
from api.rate_limiter import limiter
from schemas.plan import PlanUpdate, PlanResponse, PlanBase
from crud.plan import get_plan_by_id, update_plan, get_plan_by_name, delete_plan, create_plan

router = APIRouter(
    prefix="",
    tags=["Admin - Plans"],
    dependencies=[Depends(require_admin)]
)

@router.post("/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/minute")
def create_new_plan(
    request: Request,
    plan_data: PlanBase,
    db: Session = Depends(get_db),
):
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
@limiter.limit("20/minute")
def edit_plan(
    request: Request,
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
@limiter.limit("20/minute")
def delete_plan_by_id(
    request: Request,
    plan_id: int,
    db: Session = Depends(get_db)
):
    plan = get_plan_by_id(db, plan_id)
    if not plan:
        raise HTTPException(404, "Plan not found")
    
    delete_plan(db, plan)
    
    return {"message": "Plan deleted successfully"}
