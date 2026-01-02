# Quick Fix: Update Database Password

## The Problem
Your `.env` file still has the placeholder password: `DB_PASSWORD=your_local_password`

## The Solution

### Step 1: Open your `.env` file
Open the file: `D:\CKP\pinnacle college erp\code\.env`

### Step 2: Find this line
```
DB_PASSWORD=your_local_password
```

### Step 3: Replace it with your actual PostgreSQL password

**Example:**
If your PostgreSQL password is `mypassword123`, change it to:
```
DB_PASSWORD=mypassword123
```

**Important:** 
- No quotes needed
- No spaces around the `=`
- Use the exact password you use to connect to PostgreSQL in pgAdmin

### Step 4: Save the file

### Step 5: Test again
```bash
python manage.py migrate
```

---

## Don't Know Your Password?

### Option A: Check in pgAdmin
1. Try connecting to PostgreSQL in pgAdmin
2. The password you use there is what you need in `.env`

### Option B: Reset PostgreSQL Password
1. In pgAdmin, right-click your PostgreSQL server
2. Go to **Properties** → **Connection**
3. You can see or change the password there

### Option C: Create New User (Easier)
1. In pgAdmin: **Login/Group Roles** → Right-click → **Create** → **Login/Group Role**
2. **Name:** `pinnacle_user`
3. **Password:** `pinnacle123` (or your choice)
4. Check **Can login?** and **Create databases?**
5. Create database `pinnacle_college_db` with this user as owner
6. Update `.env`:
   ```
   DB_USER=pinnacle_user
   DB_PASSWORD=pinnacle123
   ```

---

## Quick Test Script

You can also use PowerShell to update it:

```powershell
# Replace "YOUR_PASSWORD" with your actual password
(Get-Content .env) -replace 'DB_PASSWORD=.*', 'DB_PASSWORD=YOUR_PASSWORD' | Set-Content .env
```

---

## After Updating Password

Once you update the password, run:
```bash
python manage.py migrate
```

If it works, you'll see:
```
Operations to perform:
  Apply all migrations: ...
Running migrations:
  ...
```

Then you can run:
```bash
python manage.py runserver
```

