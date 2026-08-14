# 📘 KVSP Pharmacy API Documentation

## 🔐 Authentication

### POST /auth/register

Register a new user

Request:
{
"username": "kvsp",
"password": "1234",
"role": "admin"
}

Response:
{
"message": "User registered successfully"
}

---

### POST /auth/login

Login and receive JWT token

Request:
{
"username": "admin",
"password": "1234"
}

Response:
{
"token": "JWT_TOKEN"
}

---

## 🏪 Outlet Management

### POST /outlet/add

Create a new outlet (Admin only)

Request:
{
"name": "Store A",
"location": "Hyderabad",
"type": "store"
}

---

### GET /outlet/all

Get all outlets

---

## 💊 Medicine

### POST /medicine/add

Add new medicine

Request:
{
"name": "Paracetamol",
"description": "Fever",
"price": 50,
"cost_price": 30,
"category": "tablet"
}

---

## 📦 Batch

### POST /batch/add

Add stock batch

Request:
{
"medicine_id": 1,
"batch_number": "B1",
"expiry_date": "2026-12-31",
"quantity": 100,
"outlet_id": 1
}

---

## 💰 Sales

### POST /sales/sell

Sell medicine

Request:
{
"medicine_id": 1,
"quantity": 5,
"outlet_id": 1
}

Response:
{
"message": "Sale completed",
"invoice": {
"total_price": 250,
"profit": 100
}
}

---

## 🤖 AI

### GET /ai/replenishment

Get restock suggestions

---

### GET /ai/anomalies

Detect unusual transactions

---

### POST /ai/chat

Ask business questions

Request:
{
"query": "Which medicine sold most?"
}

---

## 📊 Reports

### GET /report/revenue

### GET /report/profit

### GET /report/outlet-performance
