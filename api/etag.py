import hashlib
from fastapi import Request, HTTPException, Response
from typing import Any

def compute_etag(data: Any) -> str:
    """
    Computes an ETag string based on the given data.
    Incorporates 'updated_at' and 'created_at' if available, accounting for partial data/pagination.
    """
    def extract_state(item):
        state = []
        
        if isinstance(item, dict):
            if "id" in item:
                state.append(f"id:{item['id']}")
            if "updated_at" in item and item["updated_at"]:
                state.append(f"u:{item['updated_at']}")
            if "created_at" in item and item["created_at"]:
                state.append(f"c:{item['created_at']}")
            if "role" in item and item["role"]:
                state.append(f"r:{item['role']}")
            if "is_email_verified" in item:
                state.append(f"ev:{item['is_email_verified']}")
            if "is_active" in item:
                state.append(f"a:{item['is_active']}")
            if "status" in item:
                state.append(f"s:{item['status']}")
            if "current_plan_id" in item:
                state.append(f"p:{item['current_plan_id']}")
            if "files" in item and item["files"]:
                files_state = []
                for f in item["files"]:
                    if isinstance(f, dict):
                        f_id = f.get("file_id") or f.get("id") or ""
                        f_name = f.get("filename") or ""
                        f_size = f.get("size") or 0
                        files_state.append(f"f:{f_id}:{f_name}:{f_size}")
                if files_state:
                    state.append("|".join(files_state))
            if not state:
                # If no id/updated_at, just use the string representation
                try:
                    state.append(str(sorted(item.items())))
                except TypeError:
                    state.append(str(item))
        else:
            # Handle SQLAlchemy models or objects
            if hasattr(item, "id"):
                state.append(f"id:{item.id}")
            if hasattr(item, "updated_at") and item.updated_at:
                # handle both datetime objects and strings
                u_ts = item.updated_at.timestamp() if hasattr(item.updated_at, 'timestamp') else str(item.updated_at)
                state.append(f"u:{u_ts}")
            if hasattr(item, "created_at") and item.created_at:
                c_ts = item.created_at.timestamp() if hasattr(item.created_at, 'timestamp') else str(item.created_at)
                state.append(f"c:{c_ts}")
                
            # Add safety checks for important status fields that might change
            if hasattr(item, "is_email_verified"):
                state.append(f"ev:{item.is_email_verified}")
            if hasattr(item, "is_active"):
                state.append(f"a:{item.is_active}")
            if hasattr(item, "status"):
                state.append(f"s:{item.status}")
            if hasattr(item, "current_plan_id"):
                state.append(f"p:{item.current_plan_id}")
            if hasattr(item, "role"):
                state.append(f"r:{item.role}")
                
            if hasattr(item, "files") and item.files:
                files_state = []
                for f in item.files:
                    if hasattr(f, "file_id"):
                        f_id = getattr(f, "file_id")
                        f_name = getattr(f, "filename", "")
                        f_size = getattr(f, "size", 0)
                        files_state.append(f"f:{f_id}:{f_name}:{f_size}")
                if files_state:
                    state.append("|".join(files_state))
                
        return "|".join(state) if state else str(item)

    components = []
    
    if isinstance(data, dict):
        if "items" in data and isinstance(data["items"], list):
            for item in data["items"]:
                components.append(extract_state(item))
        if "metrics" in data and isinstance(data["metrics"], dict):
            metrics_str = ",".join(f"{k}:{v}" for k, v in sorted(data["metrics"].items()))
            components.append(f"metrics:[{metrics_str}]")
            
        if "items" not in data and "metrics" not in data:
            try:
                components.append(str(sorted(data.items())))
            except TypeError:
                components.append(str(data))
            
    elif isinstance(data, list):
        for item in data:
            components.append(extract_state(item))
            
    elif hasattr(data, "__table__"):
        components.append(extract_state(data))
        
    else:
        components.append(str(data))
        
    raw_string = "||".join(components).encode("utf-8")
    return f'W/"{hashlib.md5(raw_string).hexdigest()}"'

def check_etag(request: Request, etag: str):
    """
    Checks if the provided ETag matches the 'if-none-match' header.
    Raises a 304 exception if it matches.
    """
    if_none_match = request.headers.get("if-none-match")
    if if_none_match == etag:
        raise HTTPException(status_code=304, headers={"ETag": etag})

def compute_db_etag(
    db: Any,
    model: Any,
    page: int | None = None,
    limit: int | None = None,
    filters: list | None = None,
    order_by: Any = None
) -> str:
    """
    Computes an ETag using only the 'id' and the timestamp field ('updated_at', 'created_at', or 'sent_at')
    queried directly from the DB. This avoids fetching and serializing the entire dataset.
    """
    from sqlalchemy import func
    
    id_field = getattr(model, "id", None)
    ts_field = None
    if hasattr(model, "updated_at"):
        ts_field = model.updated_at
    elif hasattr(model, "created_at"):
        ts_field = model.created_at
    elif hasattr(model, "sent_at"):
        ts_field = model.sent_at
        
    fields = []
    if id_field is not None:
        fields.append(id_field)
    if ts_field is not None:
        fields.append(ts_field)
        
    if not fields:
        count = db.query(func.count()).select_from(model).scalar() or 0
        return f'W/"count-{count}"'
        
    query = db.query(*fields)
    
    if filters:
        for f in filters:
            query = query.filter(f)
            
    if order_by is not None:
        if isinstance(order_by, (list, tuple)):
            query = query.order_by(*order_by)
        else:
            query = query.order_by(order_by)
        
    # Get total count for pagination context
    count_query = db.query(func.count(id_field or model.id))
    if filters:
        for f in filters:
            count_query = count_query.filter(f)
    total_count = count_query.scalar() or 0
    
    if page is not None and limit is not None:
        offset = (page - 1) * limit
        query = query.offset(offset).limit(limit)
    elif limit is not None:
        query = query.limit(limit)
        
    results = query.all()
    
    components = [f"total:{total_count}"]
    for row in results:
        row_str = []
        for val in row:
            if hasattr(val, "timestamp"):
                row_str.append(str(val.timestamp()))
            else:
                row_str.append(str(val))
        components.append("-".join(row_str))
        
    raw_string = "||".join(components).encode("utf-8")
    return f'W/"{hashlib.md5(raw_string).hexdigest()}"'

def compute_global_db_etag(db: Any, models: list) -> str:
    """
    Computes a global ETag over a list of models by querying only their count and maximum timestamp.
    Extremely fast for consolidated endpoints like the dashboard.
    """
    from sqlalchemy import func
    components = []
    
    for item in models:
        if isinstance(item, tuple):
            model, filters = item
        else:
            model = item
            filters = None
            
        id_field = getattr(model, "id", None)
        ts_field = None
        if hasattr(model, "updated_at"):
            ts_field = model.updated_at
        elif hasattr(model, "created_at"):
            ts_field = model.created_at
        elif hasattr(model, "sent_at"):
            ts_field = model.sent_at
            
        count_q = db.query(func.count(id_field or model.id))
        max_q = db.query(func.max(ts_field)) if ts_field is not None else None
        
        if filters:
            for f in filters:
                count_q = count_q.filter(f)
                if max_q is not None:
                    max_q = max_q.filter(f)
                    
        count_val = count_q.scalar() or 0
        max_val = max_q.scalar() if max_q is not None else None
        
        if hasattr(max_val, "timestamp"):
            max_ts = str(max_val.timestamp())
        else:
            max_ts = str(max_val)
            
        components.append(f"{model.__tablename__}:{count_val}:{max_ts}")
        
    raw_string = "||".join(components).encode("utf-8")
    return f'W/"{hashlib.md5(raw_string).hexdigest()}"'
