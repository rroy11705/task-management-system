# Running PostgreSQL in Docker

To run a PostgreSQL container using Docker on a separate port (5434) with the container name `docker-psql`, follow these steps:

1. **Install Docker**: Ensure that Docker is installed on your machine. You can download it from [Docker's official website](https://www.docker.com/get-started).

2. **Pull the PostgreSQL Image**: Open your terminal and run the following command to pull the latest PostgreSQL image from Docker Hub:
   ```bash
   docker pull postgres
   ```

3. **Run the PostgreSQL Container**: Use the following command to run the PostgreSQL container on port 5434 with the name `docker-psql`:
   ```bash
   docker run --name docker-psql -e POSTGRES_USER=mysecretuser -e POSTGRES_PASSWORD=mysecretpassword -p 5434:5432 -d postgres
   ```
   - `--name docker-psql`: Assigns the name `docker-psql` to the container.
   - `-e POSTGRES_USER=mysecretuser`: Sets the username for the PostgreSQL superuser (you can change `mysecretuser` to your desired user).
   - `-e POSTGRES_PASSWORD=mysecretpassword`: Sets the password for the PostgreSQL superuser (you can change `mysecretpassword` to your desired password).
   - `-p 5434:5432`: Maps port 5434 on your host to port 5432 on the container (the default PostgreSQL port).
   - `-d`: Runs the container in detached mode.

4. **Access PostgreSQL**: You can connect to the PostgreSQL database using a client like `psql` or any GUI tool (e.g., pgAdmin) by connecting to `localhost:5434` with the username `postgres` and the password you set in the previous step.

5. **Stop the Container**: To stop the PostgreSQL container, run:
   ```bash
   docker stop docker-psql
   ```

6. **Remove the Container**: If you want to remove the container, use:
   ```bash
   docker rm docker-psql
   ```

Now you have PostgreSQL running in a Docker container on port 5434! Using a separate port from the default PostgreSQL port (5432) is important to avoid conflicts with any existing PostgreSQL installations on your machine.

7. **To run the Docker container in interactive mode and access the PostgreSQL shell, use the following command**:
```bash
docker exec -it docker-psql psql -U mysecretuser
```
This command allows you to interact with the PostgreSQL database directly from the command line. Make sure to replace `mysecretuser` with the username you set using the `POSTGRES_USER` environment variable.

### Viewing, Creating Databases, and Connecting with DBeaver

To connect to the PostgreSQL database using DBeaver, follow these steps:

1. **Open DBeaver**: Launch the DBeaver application on your machine.

2. **Create a New Connection**: Click on the "New Database Connection" button in the toolbar or go to `Database` > `New Database Connection`.

3. **Select PostgreSQL**: In the database selection window, choose `PostgreSQL` and click `Next`.

4. **Enter Connection Details**:
   - **Host**: `localhost`
   - **Port**: `5434`
   - **Database**: Leave this blank to connect to the default database.
   - **Username**: Enter the username you set using the `POSTGRES_USER` environment variable (e.g., `admin`).
   - **Password**: Enter the password you set using the `POSTGRES_PASSWORD` environment variable.

5. **Test Connection**: Click on the `Test Connection` button to ensure that DBeaver can connect to your PostgreSQL instance. If the connection is successful, click `Finish`.

6. **Connect to the Database**: You should now see your new connection in the Database Navigator. Double-click on it to connect.

Once connected, you can view existing databases, create new ones, and manage your PostgreSQL instance directly from DBeaver.

### Viewing and Creating Databases

Once you are in the PostgreSQL shell, you can view existing databases with the command:
```sql
\l
```
To create a new database, use the following command to create a table:
```sql
CREATE TABLE mytable (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
Replace `mytable` with your desired table name and adjust the columns as needed. After creating the database, you can connect to it using:
```sql
CREATE DATABASE mydatabase;
```
Replace `mydatabase` with your desired database name. After creating the database, you can connect to it using:
```sql
\c mydatabase
