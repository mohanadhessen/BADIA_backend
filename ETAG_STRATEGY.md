# ETag Implementation Strategy

## Overview
As requested, I've added a robust ETag caching mechanism across all eligible `GET` endpoints in the application. This ensures clients can cache responses properly and avoid re-downloading unchanged data, which saves bandwidth and improves client-side performance.

## Strategy Addressed: Partial Data & Pagination
You pointed out an important consideration:
> "make sure the data will update not just slap the updated_at as you can see some endpoit get partial data like limit to the new 25 user so make this into account so maby in the get all users you use the last user created at section if you have a nother idea"

Using the max `updated_at` or `created_at` of the entire database table isn't safe for paginated data, because adding or removing an item changes the **subset** of data shown on a specific page, even if the remaining items weren't updated.

**My Solution:**
Instead of trying to find the "latest updated" record across the entire table, I built a highly robust ETag generation utility (`api/etag.py`) that executes **after** the paginated data is retrieved from the database but **before** it's sent to the client.

The `compute_etag(data)` function traverses the returned dataset:
1. **For Lists of Data (like `limit=25`):** It extracts the `id`, `created_at`, and `updated_at` of **every single item** in that specific returned subset.
2. **For Metadata/Metrics:** If the response includes `metrics` (like `total_users`), it includes those metrics in the hash. 
3. **Hashing:** It combines all these attributes into a single string and hashes it using MD5 to generate the ETag.

### Why is this the best approach?
- **Perfect Accuracy:** If a user is added, removed, or updated on that specific page, the IDs or `updated_at` timestamps of the subset change, resulting in a completely new ETag.
- **Fast:** Hashing a small subset of 25 items takes practically zero CPU time. 
- **Bandwidth Savings:** If the ETag matches the client's `If-None-Match` header, the server skips serializing the JSON payload and throws a `304 Not Modified` exception, immediately closing the connection and saving network transfer.

## Changes Made
1. **Created Utility (`api/etag.py`):**
   - Added `compute_etag(data)` to safely hash single records, paginated datasets, and dictionaries.
   - Added `check_etag(request, etag)` which intercepts the request and raises a `304 Not Modified` if the data hasn't changed.

2. **Modified Endpoints:**
   Imported and applied this mechanism to all eligible `GET` endpoints:
   - **Users:** `GET /api/v1/users/me`, `GET /api/v1/users/me/requests`
   - **Plans:** `GET /api/v1/plans/` (upgraded existing cache logic to use the new standard utility)
   - **Admin Users:** `GET /api/v1/admin/users`, `GET /api/v1/admin/users/plan-distribution`, `GET /api/v1/admin/user`
   - **Admin Payments:** `GET /api/v1/admin/payments`
   - **Admin Requests:** `GET /api/v1/admin/requests`
   - **Admin Reviews:** `GET /api/v1/admin/reviews`
   - **Admin Storage:** `GET /api/v1/admin/storage/usage`, `GET /api/v1/admin/emails/sent-this-month`

*(Note: Endpoints returning presigned file download URLs were explicitly skipped because the URLs contain time-sensitive expiration signatures that change on every generation, rendering ETags ineffective and potentially causing clients to cache expired links).*
