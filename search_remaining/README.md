# knowledge-search-api

Setup:
Step 1: Create Env
Create a new python env with the following command. Must be created only once
python -m venv env

Step 2: Once the env folder is generated, use to following to switch into the env
./env/Scripts/activate
If the script fails to run in linux, add the additional file previlidges (right click>properties, check the "enable to run as a script option")

Step 3: Install packages into env from requirements.txt
pip install -r requirements.txt


Post Setup Notes

Run Server: Dev
uvicorn app.main:app --reload

Run Server: Prod
uvicorn app.main:app

In order to freeze all the requirements into requirements.txt, the following script comes in handy:
$PSDefaultParameterValues['Out-File:Encoding'] = 'utf8'     # if using powershell on windows, execute this first to change encoding to utf-8
pip freeze > requirements.txt

 
-----------------------------------
PackageList:
Added the following high level packages to requirements.txt:
fastapi
"uvicorn[standard]"
dataclasses
pydantic-settings
sqlalchemy
psycopg2
alembic
opensearch-py
pandas
xlsxwriter
pydantic[email]
pyjwt
requests
fastapi-cache2
pyinstrument

-----------------------------------

Python Environment Variables - Local Setup:
Create a new .env.local file in the root folder.
Maintain Multiple Environments by creating the following files
.env.local  -- to house local server environments
.env.server.dev  -- to house dev server environments
.env.server.prod  -- to house prod server environments

Default configuration points to .env.local file
In order to switch to .env.server.dev -> IN env_file variable change LOCAL to PRODUCTION.

NOTE: The aforementioned env files must not be checked into codebase as it could contain sensitive data.

Python Environment Variables - Server Setup:
Server configuration doesn't load .env.* files, but rather loads os environment variables. As such any addition of environment variables must be manages directly in the pods environment variables.

-----------------------------------

Migrations:
NOTE: For any new tables, import the model into database.py as this will be imported and run to add all the information into the metadata structure 

Generate Migrations:
The following command can be used to generate migrations - 
 alembic revision --autogenerate -m "migration-name"

To review the migration sql scripts (offline mode), run the following commands -
 alembic upgrade head --sql
The above will display the sql commands that will be run in online mode.

To apply the migrations into the db (online mode), run the following command - 
 alembic upgrade head
