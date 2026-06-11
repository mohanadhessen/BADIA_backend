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
            
        # Handle dicts (e.g., if items are serialized or raw dicts)
        if isinstance(item, dict):
            if "id" in item:
                state.append(f"id:{item['id']}")
            if "updated_at" in item and item["updated_at"]:
                state.append(f"u:{item['updated_at']}")
            if "created_at" in item and item["created_at"]:
                state.append(f"c:{item['created_at']}")
            if not state:
                # If no id/updated_at, just use the string representation
                try:
                    state.append(str(sorted(item.items())))
                except TypeError:
                    state.append(str(item))
                
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
