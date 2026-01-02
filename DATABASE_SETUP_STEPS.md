# Database Setup Steps

## Database Configuration

Based on your `.env` file, use these settings:

### Database Name
**`pinnacle_college_db`**

### Database User
**`postgres`** (or create a new user)

### Database Password
Use the password you set for the `postgres` user when you installed PostgreSQL.

---

## Step-by-Step Setup

### Option 1: Use Existing postgres User (Easiest)

1. **Open pgAdmin**
2. **Connect to your PostgreSQL server** (you'll need the postgres user password)
3. **Create the database:**
   - Right-click on **Databases** → **Create** → **Database...**
   - **Database name:** `pinnacle_college_db`
   - **Owner:** `postgres`
   - Click **Save**

4. **Update your `.env` file:**
   - Open `.env` file
   - Find the line: `DB_PASSWORD=your_local_password`
   - Replace `your_local_password` with your actual PostgreSQL `postgres` user password
   - Save the file

5. **Test the connection:**
   ```bash
   python manage.py migrate
   ```

### Option 2: Create a New Database User (Recommended for Production)

1. **Open pgAdmin**
2. **Create a new user:**
   - Right-click on **Login/Group Roles** → **Create** → **Login/Group Role...**
   - **General tab:**
     - **Name:** `pinnacle_user`
   - **Definition tab:**
     - **Password:** `pinnacle123` (or choose your own secure password)
   - **Privileges tab:**
     - Check **Can login?**
     - Check **Create databases?**
   - Click **Save**

3. **Create the database:**
   - Right-click on **Databases** → **Create** → **Database...**
   - **Database name:** `pinnacle_college_db`
   - **Owner:** Select `pinnacle_user` from dropdown
   - Click **Save**

4. **Grant permissions (if needed):**
   - Right-click on `pinnacle_college_db` → **Query Tool**
   - Run this SQL:
   ```sql
   GRANT ALL PRIVILEGES ON DATABASE pinnacle_college_db TO pinnacle_user;
   \c pinnacle_college_db
   GRANT ALL ON SCHEMA public TO pinnacle_user;
   ```

5. **Update your `.env` file:**
   ```env
   DB_NAME=pinnacle_college_db
   DB_USER=pinnacle_user
   DB_PASSWORD=pinnacle123
   DB_HOST=localhost
   DB_PORT=5433
   ```

6. **Test the connection:**
   ```bash
   python manage.py migrate
   ```

---

## Quick Reference

### If using postgres user:
```env
DB_NAME=pinnacle_college_db
DB_USER=postgres
DB_PASSWORD=YOUR_POSTGRES_PASSWORD_HERE
DB_HOST=localhost
DB_PORT=5433
```

### If using new user:
```env
DB_NAME=pinnacle_college_db
DB_USER=pinnacle_user
DB_PASSWORD=pinnacle123
DB_HOST=localhost
DB_PORT=5433
```

---

## After Setup

Once the database is created and password is updated:

1. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

2. **Create superuser (optional):**
   ```bash
   python manage.py createsuperuser
   ```

3. **Run server:**
   ```bash
   python manage.py runserver
   ```

4. **Access the application:**
   - Open browser: http://127.0.0.1:8000
   - Or: http://localhost:8000

---

## Troubleshooting

### "password authentication failed"
- Make sure the password in `.env` matches your PostgreSQL user password exactly
- Check for extra spaces in the password

### "database does not exist"
- Make sure you created the database `pinnacle_college_db` in pgAdmin
- Check the database name matches exactly (case-sensitive)

### "connection refused"
- Make sure PostgreSQL service is running
- Check if PostgreSQL is actually running on port 5433
- In pgAdmin, check server properties to confirm the port

