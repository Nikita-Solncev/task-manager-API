from dotenv import dotenv_values

data = dotenv_values(".env")

class Config:
    SQLALCHEMY_DATABASE_URI = data["SQLALCHEMY_DATABASE_URI"]
    SECRET_KEY = data["SECRET_KEY"] 
    JWT_SECRET_KEY = data["JWT_SECRET_KEY"]