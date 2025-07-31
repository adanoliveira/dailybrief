# Database Connection Guide

This guide provides instructions for connecting to the DailyBrief PostgreSQL database using popular SQL clients.

## Connection Details

- **Host:** localhost
- **Port:** 5432
- **Database:** dailybrief
- **Username:** postgres
- **Password:** postgres
- **Connection URL:** `postgresql://postgres:postgres@localhost:5432/dailybrief`

## DBeaver

1. Download and install [DBeaver](https://dbeaver.io/)
2. Click "New Database Connection" 
3. Select "PostgreSQL"
4. Enter the connection details:
   - Host: localhost
   - Port: 5432
   - Database: dailybrief
   - Username: postgres
   - Password: postgres
5. Test the connection and click "Finish"

## TablePlus

1. Download and install [TablePlus](https://tableplus.com/)
2. Click "Create a new connection"
3. Select "PostgreSQL"
4. Enter the connection details:
   - Name: DailyBrief Local
   - Host: localhost
   - Port: 5432
   - User: postgres
   - Password: postgres
   - Database: dailybrief
5. Test the connection and click "Connect"

## pgAdmin

1. Download and install [pgAdmin](https://www.pgadmin.org/)
2. Right-click on "Servers" and select "Create" → "Server"
3. On the General tab, enter "DailyBrief Local" as the name
4. On the Connection tab, enter:
   - Host: localhost
   - Port: 5432
   - Maintenance database: dailybrief
   - Username: postgres
   - Password: postgres
5. Click "Save"

## Visual Studio Code (with PostgreSQL extension)

1. Install the [PostgreSQL extension](https://marketplace.visualstudio.com/items?itemName=ckolkman.vscode-postgres) for VS Code
2. Click on the PostgreSQL icon in the sidebar
3. Click "+" to add a new connection
4. Enter the connection details:
   - Host: localhost
   - Port: 5432
   - Database: dailybrief
   - Username: postgres
   - Password: postgres
5. Save the connection

## Command Line (psql)

Connect directly using psql:

```bash
psql -h localhost -p 5432 -d dailybrief -U postgres
```

Or using the connection string:

```bash
psql "postgresql://postgres:postgres@localhost:5432/dailybrief"
```

## Docker Container Direct Access

To access the PostgreSQL instance directly from the container:

```bash
# Connect to PostgreSQL inside the container
docker exec -it dailybrief-db-1 psql -U postgres -d dailybrief

# Run SQL commands inside the container
docker exec -it dailybrief-db-1 psql -U postgres -d dailybrief -c "SELECT * FROM articles_article LIMIT 5;"

# Export data
docker exec -it dailybrief-db-1 pg_dump -U postgres -d dailybrief > dailybrief_backup.sql
```

## Troubleshooting Connection Issues

1. **Container not running**: Ensure Docker is running and the database container is up:
   ```bash
   docker ps | grep postgres
   ```

2. **Port conflict**: Check if another service is using port 5432:
   ```bash
   lsof -i :5432
   ```

3. **Network issue**: Verify the Docker network configuration:
   ```bash
   docker network inspect dailybrief_default
   ```

4. **Database initialization**: If the database is new, it might need initialization:
   ```bash
   docker-compose up -d db
   docker-compose exec backend python manage.py migrate
   ```

5. **Connection refused**: Make sure the PostgreSQL service is accepting connections:
   ```bash
   docker-compose logs db
   ``` 