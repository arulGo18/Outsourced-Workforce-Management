# Outsourced Workforce Management System

A web-based **Outsourced Workforce Management System** designed to support workforce administration for **e-commerce warehouse operations**. This system helps manage outsourced workers, worker ID verification, workforce planning, and operational activities through dedicated interfaces for administrators and vendor PICs.

---

## Overview

This project was developed as part of my Information Systems portfolio and focuses on digitizing the outsourcing workforce management process.

The application provides two separate user roles:

- **Administrator Warehouse**
- **Vendor PIC (Person In Charge)**

The backend is built with **FastAPI** and **PostgreSQL**, while the frontend uses **HTML**, **CSS**, and **JavaScript** and **Python**.

---

## Features

### Administrator

- Dashboard overview
- Worker management
- Workforce planning
- Buffer worker management
- Worker ID verification
- Workforce activity monitoring
- Contract management
- Take Out management
- Account management

### Vendor PIC

- Dashboard
- Register new workers
- Worker data management
- Worker ID activation
- Worker mutation
- Contract updates
- Activity monitoring
- Account management

---

## Tech Stack

### Backend

- FastAPI
- SQLAlchemy
- PostgreSQL
- Pydantic
- Uvicorn
- Python

### Frontend

- HTML5
- CSS3
- JavaScript

### Other Tools

- Git
- GitHub
- VS Code

---

## Project Structure

```
.
├── backend
│   ├── routes
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   └── main.py
│
├── frontend
│   ├── admin
│   └── vendor
│
└── requirements.txt
```

---

# System Architecture

```
Browser
      │
      ▼
Frontend (HTML, CSS, JavaScript)
      │
      ▼
FastAPI REST API
      │
      ▼
PostgreSQL Database
```

---

# Screenshots

## Administrator Dashboard

<p align="center">
<img src="images/admin-dashboard.png" width="900">
</p>

---

## Vendor PIC Dashboard

<p align="center">
<img src="images/vendor-dashboard.png" width="900">
</p>

---

## FastAPI Server Running

<p align="center">
<img src="images/server-running.png" width="900">
</p>

# Requirements

- Python 3.10+
- PostgreSQL
- Git

---

# Current Deployment

This project is currently intended for **local deployment**.

The FastAPI application runs on the developer's laptop and serves as the local application server connected to a PostgreSQL database.

---

# Future Improvements

- Docker containerization
- Cloud deployment
- Authentication with JWT
- Role-based authorization
- Dashboard analytics
- Email notifications
- Mobile responsive improvements

---

# Author

**Ilyas Yasin Nurulah**

Informatics engineering Student

Backend Development • Data Analysis • Information Systems
