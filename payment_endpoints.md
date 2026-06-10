# Admin Payments API Endpoints

This document outlines the API endpoints added for handling payments under the Admin router (`/api/v1/admin/payments`).

## 1. Create Payment

Create a new payment record manually. If successfully created, an email with the payment receipt is sent to the user as a background task.

- **Endpoint:** `POST /`
- **Authentication:** Admin privileges required.
- **Request Body (JSON):**
```json
{
  "user_id": 123,
  "plan_id": 456,
  "amount": 99.99,
  "billing_cycle": "monthly", // or "yearly"
  "start_date": "2026-06-11T00:00:00Z",
  "end_date": "2026-07-11T00:00:00Z"
}
```
- **Success Response (200 OK):**
```json
{
  "message": "Payment created successfully",
  "payment_id": 789
}
```
- **Error Response (400 Bad Request):** Returned if the user or plan is not found, or if the billing cycle is invalid.

---

## 2. Update Payment Status

Update the status of an existing payment. Depending on the new status, an email may be dispatched to the user as a background task:
- If `"paid"`: Sends an email with the payment receipt.
- If `"canceled"`: Sends a cancellation email indicating the plan was cancelled by an admin.

- **Endpoint:** `PATCH /{payment_id}/status`
- **Authentication:** Admin privileges required.
- **Path Parameters:** 
  - `payment_id` (integer)
- **Request Body (JSON):**
```json
{
  "status": "paid" // can be "paid", "rejected", or "canceled"
}
```
- **Success Response (200 OK):**
```json
{
  "message": "Payment status updated successfully",
  "payment_id": 789,
  "status": "paid" // or "canceled", etc.
}
```
- **Error Response (400 Bad Request):** Returned if the payment is not found or the provided status is invalid.

---

## 3. Payments Telemetry

Retrieve statistics and telemetry for all payments, grouped by their payment status.

- **Endpoint:** `GET /telemetry`
- **Authentication:** Admin privileges required.
- **Request Body:** None
- **Success Response (200 OK):**
```json
{
  "total_payments": 150,
  "by_status": {
    "paid": 120,
    "rejected": 20,
    "canceled": 10
  }
}
```
