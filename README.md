# 🏥 Pharmacy Operations Platform – MedixHub Distributors

## 📌 Overview
**MedixHub Distributors Pharmacy Operations Platform** is a scalable, ready-product enterprise web application designed to unify and streamline pharmacy operations across central warehouses, hospital outlets, and retail branches.

It features a **modern dark-mode web portal**, point-of-sale (POS) billing counter, real-time inventory and expiry tracking, executive business analytics, and an **AI Operations Hub** with LLM conversational intelligence, demand forecasting, fraud/anomaly detection, and automated stock replenishment.

---

## 🚀 Key Features

### 🔐 1. Authentication & Role-Based Access Control (RBAC)
- Secure JWT-based authentication (`/auth/login`, `/auth/register`).
- Role-specific workflows for **Admin**, **Pharmacist**, **Warehouse Manager**, and **Finance Manager**.

### 🧾 2. Point of Sale (POS) Billing Counter
- Rapid medicine lookup with price, cost price, and stock validation.
- Automatic **FIFO (First-In, First-Out)** batch inventory deduction based on earliest expiry.
- Live subtotal, grand total, and profit margin calculation.
- Tax invoice generation with printable receipt view modal (`INV-XXXXXX`).

### 📦 3. Inventory & Expiry Management
- Medicine Master Catalog management.
- Batch intake recording with batch number, quantity, destination outlet, and expiry date.
- Automated warning alerts for batches expiring within 30 days.

### 📊 4. Executive Analytics & Reporting
- Real-time revenue and net estimated profit tracking.
- Interactive Chart.js charts for quarterly revenue trends and outlet performance comparisons.
- Top 5 best-selling medicines donut chart.

### 🤖 5. Medix AI Operations Hub & LLM Service
- **Conversational AI Assistant**: Natural language query engine connected to a local LLM (Ollama `phi3`) and database analytics rule engine (`/ai/chat`).
- **Demand Prediction**: Machine learning linear regression model predicting future unit demand (`/ai/predict/<id>`).
- **Fraud & Anomaly Detection**: Isolation Forest ML model scanning transaction logs for price/quantity outliers (`/ai/anomalies`).
- **Automated Replenishment**: Reorder quantity suggestions when stock falls below predicted demand (`/ai/replenishment`).

---

## 🛠️ Tech Stack

- **Frontend**: HTML5, Vanilla CSS3 (Custom Glassmorphism Enterprise Theme, Dark Palette), ES6+ JavaScript, Chart.js.
- **Backend**: Python (Flask microservices framework, Flask-CORS, PyJWT, Bcrypt, SQLAlchemy).
- **LLM AI Engine**: Ollama (`phi3` / `llama3`) running locally at `http://localhost:11434`.
- **Database**:
  - **Local Development**: SQLite (`pharmacy.db`) with zero manual database setup.
  - **Production**: PostgreSQL (configured via `DATABASE_URL` environment variable).
- **AI & Analytics**: Scikit-Learn (Linear Regression & Isolation Forest), Pandas, NumPy.
- **Deployment**: Docker, Docker Compose, WSGI / Waitress / Gunicorn.

---

## 🤖 Setting Up the LLM Service (Ollama Guide)

The **Medix AI Assistant** uses **Ollama** to run local Large Language Models (`phi3`, `llama3`, or `mistral`) completely offline and privately without needing external API keys.

### 📥 1. Download & Install Ollama
- Go to [ollama.com/download](https://ollama.com/download) and install Ollama for Windows, Mac, or Linux.

### 📦 2. Download the Model (`phi3`)
Open your terminal or Command Prompt and run:
```bash
ollama pull phi3
```
*(Optionally, you can pull `llama3` or `mistral`: `ollama pull llama3`)*

### 🚀 3. Start the Ollama Server
Ensure the Ollama service is running in the background:
```bash
ollama serve
```
*Verify it is running by opening `http://localhost:11434` in your web browser.*

### 💡 How the AI Assistant Operates:
- **Hybrid AI Architecture**:
  - For exact data queries (e.g., *"What is our total revenue?"*, *"Which medicine sold most?"*, *"Which batches expire soon?"*), the system queries the live database and returns instant structured reports.
  - For general business questions or operational advice, the system routes queries to your local **Ollama `phi3`** model.

---

## ⚡ How to Run the Application on Any System

### 📋 Prerequisites
- **Python 3.10+** installed.
- **VS Code** (or any code editor / terminal).
- **Ollama** (Optional, for LLM chat features).
- **Web Browser** (Chrome, Edge, Safari, Firefox).

---

### 🚀 Quick Start (VS Code / Local Machine)

1. **Open Project in VS Code**:
   Launch VS Code and open the `Medixhub-phramcy-operations-main` folder (`File -> Open Folder...`).

2. **Install Python Dependencies**:
   Open the VS Code Terminal (`Ctrl + ~`) and run:
   ```bash
   python -m pip install -r requirements.txt
   ```

3. **Launch Application**:
   Run the unified Flask server in the terminal:
   ```bash
   python backend/app.py
   ```

4. **Open Web Portal**:
   Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

---

### 📱 Accessing from Other Devices (Phones / Tablets / Laptops on Same Wi-Fi)

1. Find your computer's local IP address using `ipconfig` (Windows) or `ifconfig` (Mac/Linux).
2. On any phone, tablet, or laptop connected to the same Wi-Fi, open the browser to:
   ```
   http://<YOUR_LOCAL_IP>:5000
   ```
   *(Example: `http://192.168.1.15:5000`)*

---

### 💾 Zero Database Configuration
- **SQLite Out-Of-The-Box**: No PostgreSQL installation required for local testing. SQLAlchemy automatically creates `pharmacy.db` and all required tables upon starting.
- **PostgreSQL Production Switch**: To connect to PostgreSQL in production, set the environment variable:
  ```powershell
  $env:DATABASE_URL="postgresql://postgres:admin7777@localhost:5432/pharmacy_db"
  ```

---

## 📖 How to Use the Application (User Guide)

1. **Login / User Roles**:
   - Click **Login / Register** in the top right header.
   - Select your role: **Admin**, **Pharmacist**, **Warehouse**, or **Finance**.

2. **POS Billing Counter**:
   - Switch to the **POS Billing Counter** tab on the sidebar.
   - Select a medicine and quantity. The system automatically checks stock across active batches.
   - Click **Complete Sale & Generate Invoice** to deduct stock and generate a printable tax invoice.

3. **Managing Stock Batches**:
   - Go to **Medicines & Stock** tab.
   - Click **Receive New Stock Batch** to add batch numbers, quantities, destination outlets, and expiry dates.

4. **Asking the AI Assistant**:
   - Navigate to the **Medix AI Operations Hub** tab.
   - Ask questions like:
     - *"What is our total revenue?"*
     - *"Which medicine sold the most?"*
     - *"What medicines are low in stock?"*
     - *"What is our estimated profit margin?"*

---

## 📂 Project Structure

```
Medixhub-phramcy-operations-main/
│── frontend/                      # Web Portal UI (HTML, CSS, JS)
│   ├── css/
│   │   └── styles.css             # Glassmorphism dark enterprise theme
│   ├── js/
│   │   ├── api.js                 # API client wrapper & JWT auth handler
│   │   ├── app.js                 # Main application controller & charts
│   │   └── demo_data.js           # Offline seed/mock dataset
│   └── index.html                 # Single-Page Application (SPA)
│
│── backend/                       # Flask Microservices & REST APIs
│   ├── app.py                     # Main application entry point & router
│   ├── database.py                # SQLAlchemy engine & SQLite/Postgres fallback
│   ├── services/
│   │   ├── ai_service/            # LLM service (Ollama), demand prediction, anomaly scan, AI chat
│   │   ├── auth_service/          # JWT auth, user registration, role checks
│   │   ├── inventory_service/     # Medicine master, batch intake, outlets
│   │   └── sales_service/         # POS billing, FIFO deduction, reports
│   └── shared/                    # Middleware, audit logs, and loggers
│
│── pharmacy.db                    # Local SQLite database (Auto-generated)
│── docker-compose.yml             # Docker multi-container deployment configuration
│── requirements.txt               # Python package dependencies
└── README.md                      # Comprehensive project documentation
```

---

## 📌 Conclusion
This platform provides an end-to-end, production-grade, AI-powered solution for modern pharmacy operations. It eliminates manual bookkeeping, speeds up billing counter operations, prevents stockouts, and delivers executive decision insights.

---

## 👤 Author
**KOLA VENKATA SAI PUTRAYYA**
