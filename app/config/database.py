# database.py
import json
import json
from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
import os

from sqlalchemy.ext.asyncio.session import AsyncSession

Base = declarative_base()

class Database:
    engine = None
    SessionEngine = None

    @staticmethod
    async def _load_from_secret_manager() -> None:
        import httpx
        try:
            aws_session_token = os.environ.get('AWS_SESSION_TOKEN')
            parameter_key = os.environ.get('PARAMETER_STORE_KEY')
            
            # Using httpx for better security and consistency
            url = "http://localhost:2773/systemsmanager/parameters/get"
            headers = {'X-Aws-Parameters-Secrets-Token': aws_session_token}
            params = {'name': parameter_key}
            
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=headers, params=params)
                resp.raise_for_status()
                data = resp.json()
                
            config = json.loads(data['Parameter']['Value'])
            os.environ.update(config)
        except httpx.HTTPError as e:
            print("HTTP error occurred:", e)
        except Exception as e:
            print("An error occurred loading secrets:", e)

    @staticmethod
    async def init_database() -> None:
        if os.getenv('AWS_LAMBDA_FUNCTION_NAME') is not None:
            await Database._load_from_secret_manager()
        db_url = f"{os.getenv('DB_DRIVER_ASYNC')}://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
        Database.engine = create_async_engine(db_url)

    @staticmethod
    def get_session():
        if Database.SessionEngine is None:
            Database.SessionEngine = sessionmaker(bind=Database.engine, class_=AsyncSession)
        return Database.SessionEngine

    @staticmethod
    async def get_instance() -> AsyncGenerator[AsyncSession, None]:
        async_session_local = Database.get_session()
        async with async_session_local() as session:
            yield session
