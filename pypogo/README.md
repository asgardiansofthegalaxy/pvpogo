# Project Setup Guide

This guide outlines the steps to set up and run the project on your local machine.

## Prerequisites

Before you begin, make sure you have the following installed:
- Python
- pip (Python package manager)
- Homebrew (for macOS users)
- MySQL

## Installation

Follow these steps to install the necessary components:

### For macOS Users:

1. Install MySQL:
    ```
    brew install mysql
    ```

2. Start MySQL service:
    ```
    brew services start mysql
    ```

3. Install  `pkg-config`:
    ```
    brew install pkg-config
    ```

4. Install PostgreSQL development files:
    ```
    sudo apt-get install libpq-dev
    ```

### Database Setup

1. Access MySQL with the following command and enter your root password:
    ```
    mysql -u root -p
    ```

2. Once in the MySQL command line, you can list all databases:
    ```
    SHOW DATABASES;
    ```

3. Select your database:
    ```
    USE PVPOGO;
    ```

### MODIFY AND MIGRATE DATABASE

1. Change your models in `models.py`

2. Create migrations for those changes:
    `python manage.py makemigrations`

3. Apply those changes to the database:
    `python manage.py migrate`

4. Run the development server:
    `python manage.py runserver`

5. Open a web browser and navigate to /admin/ on your local domain (e.g., http://127.0.0.1:8000/admin/).

### MANAGEMENT COMMANDS

The BaseCommand class in Django serves as the cornerstone for developing bespoke management commands accessible through the Django management interface. This flexibility allows for the extension of Django's inbuilt command suite to suit our specific project needs.

Within the pokexperience project structure, navigate to the management directory located inside the pokexperience folder. Further within, you'll find the commands subdirectory, which houses the load_json_to_db.py script. This script is designed to facilitate the loading of Pokemon and Move data from JSON files directly into the database, leveraging Django's ORM capabilities.

The core functionality of the script resides within the handle() method. Here, we define the specific operations that our custom command will perform upon execution. This method acts as the entry point for the command's logic, ensuring that our script executes as intended when invoked.

For detailed information on the command's purpose and usage, the following command can be executed:

```
python manage.py help load_json_to_db
```

To execute the custom command and commence the data loading process, use the manage.py script followed by the command's name, as shown below:

```
python manage.py load_json_to_db
```

This command will initiate the script, leveraging Django's management framework to process and insert the specified JSON data into our project's database.