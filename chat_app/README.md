python -m venv env

./env/Scripts/activate

pip install chromadb
pip install langgraph==0.1.17
pip install langgraph-checkpoint-sqlite

# to run api
uvicorn main:app --reload
# to add new lib to requirements.txt
pip freeze > requirements.txt

alembic revision --autogenerate -m "Add ragas_evaluation table"
alembic upgrade head