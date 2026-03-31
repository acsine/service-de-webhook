from app.main import app, handler
import os
from dotenv import load_dotenv

if os.getenv('AWS_LAMBDA_FUNCTION_NAME') is None:
    load_dotenv()
