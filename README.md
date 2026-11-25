# BENZ Coffee Inventory Management System
## Developer and Testing Team Setup Guide

This README explains how to download, configure, run, and test the BENZ Coffee Inventory Management System on a Windows laptop.

The system consists of two separate projects:

- **Backend:** Django and Django REST Framework
- **Frontend:** Flutter

The backend handles database operations, authentication, inventory management, recipes, production, and API requests. The frontend provides the user interface used to interact with the system.

---

# 1. Prerequisites

Before setting up the project, make sure the testing laptop has the following installed:

| Software | Purpose |
|---|---|
| Git | Download and manage project source code |
| Python | Run the Django backend |
| Flutter SDK | Run the Flutter frontend |
| Android Studio or Visual Studio | Optional, depending on the Flutter target |
| Visual Studio Code | Recommended code editor |

Verify the installations using PowerShell:

```powershell
git --version
python --version
flutter --version
```

---

# 2. Download the Projects from GitHub

The frontend and backend are maintained in separate GitHub repositories.

Create a folder where both projects will be stored.

For example:

```powershell
mkdir BENZ-Testing
cd BENZ-Testing
```

### 2.1 Clone the Backend

```powershell
git clone https://github.com/TDJosh-56/BACKEND-Benz_InventorySystem.git
```

Enter the backend directory:

```powershell
cd BACKEND-Benz_InventorySystem
```

Check the current branch:

```powershell
git branch
```

The project should use the latest `main` branch.

If necessary:

```powershell
git switch main
git pull origin main
```

### 2.2 Clone the Frontend

Return to the parent folder:

```powershell
cd ..
```

Clone the Flutter frontend:

```powershell
git clone https://github.com/Masternightsky/benz_coffee_app.git
```

Enter the frontend directory:

```powershell
cd benz_coffee_app
```

Update the project:

```powershell
git switch main
git pull origin main
```

### 2.3 Expected Folder Structure

After cloning both repositories:

```text
BENZ-Testing/
│
├── BACKEND-Benz_InventorySystem/
│   ├── manage.py
│   ├── requirements.txt
│   ├── config/
│   ├── app_settings/
│   └── ...
│
└── benz_coffee_app/
    ├── pubspec.yaml
    ├── lib/
    ├── android/
    ├── windows/
    └── ...
```

---

# 3. Backend Setup (Django)

The backend must be running before the Flutter application can communicate with it.

Open a PowerShell terminal and navigate to the backend directory:

```powershell
cd BENZ-Testing\BACKEND-Benz_InventorySystem
```

### 3.1 Create a Python Virtual Environment

Create an isolated Python environment:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Then activate again:

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3.2 Install Backend Dependencies

If the repository contains `requirements.txt`, install its dependencies:

```powershell
pip install -r requirements.txt
```

If the project uses a different dependency installation method, follow the backend repository's instructions.

### 3.3 Configure the Database

The local development setup uses SQLite.

Apply database migrations:

```powershell
python manage.py makemigrations
python manage.py migrate
```

**Important:** `makemigrations` is normally only necessary when model changes have not already been included in the repository. Do not create unnecessary migrations during testing. Applying existing migrations with `migrate` is the normal setup step.

### 3.4 Create a Django Superuser

Create an administrator account for accessing the Django administration panel:

```powershell
python manage.py createsuperuser
```

Follow the prompts:

```text
Username:
Email address:
Password:
Password (again):
```

Use your own testing credentials and keep them secure.

The superuser account is intended for Django administration. It should not automatically be assumed to be the same as the application's normal login account.

### 3.5 Run the Backend Server

Start Django:

```powershell
python manage.py runserver
```

The backend should be accessible at:

```text
http://127.0.0.1:8000/
```

The API base address is:

```text
http://127.0.0.1:8000/api/
```

Keep this terminal open while testing the Flutter application.

### 3.6 Access Django Admin

Open a browser and visit:

```text
http://127.0.0.1:8000/admin/
```

Log in using the Django superuser credentials created earlier.

---

# 4. Frontend Setup (Flutter)

Open a **second PowerShell terminal**. Do not close the backend terminal.

Navigate to the Flutter project:

```powershell
cd BENZ-Testing\benz_coffee_app
```

### 4.1 Install Flutter Dependencies

Run:

```powershell
flutter pub get
```

This downloads the dependencies declared in `pubspec.yaml`.

### 4.2 Configure the Backend API Address

Before running the application, verify the API base URL in the Flutter project's API configuration.

The local backend address is:

```text
http://127.0.0.1:8000/api/
```

Make sure the Flutter application uses the correct address.

For a Windows desktop application running on the same laptop, `127.0.0.1` is suitable.

Do not change the API address unless the backend is running on a different device or address.

### 4.3 Enable Windows Desktop Support

If Windows desktop support has not been enabled:

```powershell
flutter config --enable-windows-desktop
```

Check available devices:

```powershell
flutter devices
```

### 4.4 Run the Flutter Application

Run the application on Chrome:

```powershell
flutter run -d web-server --web-port 5000 
```

Wait for Flutter to build and launch the application.

The frontend should now communicate with the Django backend.

---

# 5. Testing Workflow

Follow this order when testing the application.

## Step 1: Start the Backend

Open the backend project and run:

```powershell
python manage.py runserver
```

Confirm that Django starts without errors.

## Step 2: Start the Frontend

Open another terminal and run:

```powershell
flutter run -d web-server --web-port 5000 
```

Confirm that the application launches successfully.

## Step 3: Test Application Features

The testing team should verify the following features according to the available application functionality:

| No. | Feature | Expected Result |
|---|---|---|
| 1 | Application Launch | Frontend opens successfully |
| 2 | Login | Valid credentials allow access |
| 3 | Invalid Login | Incorrect credentials are rejected |
| 4 | Settings | Settings information loads correctly |
| 5 | Passcode Verification | Correct passcode is accepted |
| 6 | Invalid Passcode | Incorrect passcode is rejected |
| 7 | Recovery Verification | Valid recovery code is accepted |
| 8 | Passcode Reset | New passcode can be established |
| 9 | Change Passcode | Existing passcode can be changed |
| 10 | Inventory | Inventory information loads and updates correctly |
| 11 | Recipes | Recipe information is displayed correctly |
| 12 | Production | Production operations work as expected |
| 13 | Reports | Report information is displayed correctly |
| 14 | Audit Logs | Relevant system activities are recorded |

Only test features that are implemented and available in the current build.

## Step 4: Record Issues

If a feature does not work as expected, record:

- Feature being tested
- Steps performed
- Expected result
- Actual result
- Error message or screenshot
- Whether the issue occurs consistently

Do not immediately modify source code when an error occurs. Report the issue first so the development team can identify whether it originates from the frontend, backend, database, or API integration.

---

# 6. Common Issues and Solutions

### Backend cannot connect to the database

Check whether migrations have been applied:

```powershell
python manage.py migrate
```

### Flutter cannot connect to Django

Check the following:

1. Django is running.
2. The API base URL is correct.
3. The frontend and backend are running on the expected ports.
4. The backend terminal does not show an API error.

### Flutter dependencies are missing

Run:

```powershell
flutter pub get
```

### Python dependencies are missing

Activate the virtual environment and run:

```powershell
pip install -r requirements.txt
```

### Django reports missing migrations

Check the migration status:

```powershell
python manage.py showmigrations
```

Apply pending migrations:

```powershell
python manage.py migrate
```

---

# 7. Important Testing Guidelines

1. Always start the Django backend before running the Flutter frontend.
2. Keep both terminal windows open while testing.
3. Use the designated testing database and credentials.
4. Do not delete or modify database files without authorization.
5. Do not commit test credentials, passwords, or secret keys to GitHub.
6. Do not push changes directly to the `main` branch.
7. Report bugs with screenshots and reproducible steps.
8. Inform the development team before modifying backend or frontend source code.

---

# 8. Stopping the Application

When testing is complete:

1. Close the Flutter application.
2. Go to the Flutter terminal and press `Ctrl + C` if necessary.
3. Go to the Django terminal and press `Ctrl + C`.
4. Deactivate the Python virtual environment:

```powershell
deactivate
```

---

# 9. Quick Start Reference

For subsequent testing sessions, once the projects have been installed and configured:

**Terminal 1 – Backend**

```powershell
cd BENZ-Testing\BACKEND-Benz_InventorySystem
.\.venv\Scripts\Activate.ps1
python manage.py runserver
```

**Terminal 2 – Frontend**

```powershell
cd BENZ-Testing\benz_coffee_app
flutter run -d windows
```

Both applications must be running for the system to work correctly.

---

**BENZ Coffee Inventory Management System**  
Developer and Testing Team Documentation
