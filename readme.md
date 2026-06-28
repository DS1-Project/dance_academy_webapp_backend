# ⚙️ DanceAcademyApp - Backend API 🛡️

This is the robust and scalable REST API that powers the entire ecosystem of **DanceAcademyApp**. It provides secure user authentication, Role-Based Access Control (RBAC), transactional management for choreography purchases, and optimized SQL aggregations for commercial statistical reporting.

---

## 🛠️ Tech Stack

* **Language:** Python 3.11+ 🐍
* **Main Framework:** Django 5.0 + Django REST Framework (DRF)
* **Relational Database:** PostgreSQL (Supabase / Local)
* **Authentication:** JWT (JSON Web Tokens) via `djangorestframework-simplejwt`
* **Testing:** Django Test Cases (Unit & Integration tests)

---

## 📦 Project Structure

```text
backend/
├── core/                        # Global Django configuration (settings, urls, wsgi/asgi)
├── apps/                        # Modular business domain applications
│   ├── authentication/          # User profiles, Registration, Login, JWT, and RBAC (Admin, Director, Teacher, Client)
│   ├── choreography/            # Catalog of songs, video streaming logs, reviews, and statistics
│   └── sales/                   # Invoicing, Sales, details, and simulated payment gateway
├── env/                         # Virtual environment directory (isolated dependencies)
├── .env                         # Hidden local file containing secure database keys and credentials
├── .env.example                 # Template for required environment connection strings
├── manage.py                    # Django Command Line Interface (CLI)
└── requirements.txt             # Project dependencies and packaged libraries
└── .env.example         # Plantilla de secretos e hilos de conexión a la BD
```

## ⚙️  Configuration & Local Installation
Follow these detailed steps to set up the environment and run the development server on your machine:

1. Navigate to the Backend Directory
Open your terminal and enter the project backend root folder:

```Bash
cd dance_academy_webapp_backend
```
2. Activate the Virtual Environment
Activate your existing env folder based on your Operating System and chosen terminal:

In Windows (Command Prompt / CMD):

```DOS
env\Scripts\activate
```
In Windows (PowerShell):

```PowerShell
.\env\Scripts\Activate.ps1
```
In macOS / Linux / Git Bash:

```Bash
source env/bin/activate
```
(Once activated, you will see (env) at the beginning of your terminal line).

3. Install Project Dependencies
Ensure pip is upgraded and install all required external libraries:

```Bash
pip install --upgrade pip
pip install -r requirements.txt
```
4. Configure Environment Variables
Create a file named .env in the root backend directory (at the same level as manage.py) using .env.example as a template. Populate it with your custom Django secrets and Supabase credentials:

```Plaintext
DEBUG=True
SECRET_KEY=your_custom_django_secret_key_here

DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_secure_supabase_password
DB_HOST=your_project_reference.supabase.co
DB_PORT=5432
```
5. Execute Database Migrations
Prepare the schemas and deploy the relational entity model onto your PostgreSQL database:

```Bash
python manage.py makemigrations authentication choreography sales
python manage.py migrate
```
6. Start the Development Server
Launch the local Django development environment:
```
Bash
python manage.py runserver
```
The API will initialize successfully and listen for incoming HTTP requests at: http://127.0.0.1:8000/api/

## 🧪 Running Automated Tests
To verify database integrity, route protection safety, RBAC permissions constraints, and proper endpoint request-response structures, run the testing suite:

```Bash
python manage.py test
```
### 👥 Backend Contributors
Back-end Engineering Team:

CAMILO ANDRES RISCANEVO COTRINA

BRAYAN FERNANDO CRUZ PUERTA

FREDDY ALEXANDER MELO BUITRAGO

VICTORIA YUAN CHEN

YISEIRI YANUA SATIZABAL ORTIZ