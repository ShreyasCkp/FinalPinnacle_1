# Local Development Setup - Quick Fix

## Issue: 400 Bad Request Error

The error occurs because the database connection is failing. Follow these steps:

## Step 1: Update Database Password in .env

Edit your `.env` file and update the database password:

```env
DB_PASSWORD=your_actual_postgres_password
```

Replace `your_actual_postgres_password` with the password you set for PostgreSQL.

## Step 2: Verify Database Exists

1. Open **pgAdmin**
2. Connect to your PostgreSQL server
3. Check if database `pinnacle_college_db` exists
4. If not, create it:
   - Right-click **Databases** → **Create** → **Database**
   - Name: `pinnacle_college_db`
   - Owner: `postgres` (or your user)
   - Click **Save**

## Step 3: Test Database Connection

Run this command to test the connection:

```bash
python manage.py dbshell
```

If it connects successfully, you're good! Press `\q` to exit.

## Step 4: Run Migrations

```bash
python manage.py migrate
```

## Step 5: Create Superuser (Optional)

```bash
python manage.py createsuperuser
```

## Step 6: Run Development Server

```bash
python manage.py runserver
```

Then visit: http://127.0.0.1:8000 or http://localhost:8000

## Common Issues

### Issue: "password authentication failed"
- **Solution**: Check your `.env` file - make sure `DB_PASSWORD` matches your PostgreSQL password

### Issue: "database does not exist"
- **Solution**: Create the database in pgAdmin (see Step 2)

### Issue: "connection refused"
- **Solution**: Make sure PostgreSQL service is running
- On Windows: Check Services → PostgreSQL

### Issue: Still getting 400 error
- **Solution**: Check Django logs in the terminal where you ran `runserver`
- Look for specific error messages

## Current .env Configuration

Your `.env` file should have:

```env
DEBUG=True
DJANGO_ENV=local
ALLOWED_HOSTS=localhost,127.0.0.1
SITE_URL=http://localhost:8000
DB_NAME=pinnacle_college_db
DB_USER=postgres
DB_PASSWORD=YOUR_ACTUAL_PASSWORD_HERE
DB_HOST=localhost
DB_PORT=5432
```

## Quick Test

After updating the password, test with:

```bash
python manage.py check
python manage.py migrate
python manage.py runserver
```

If all three commands work, you should be able to access the UI!

