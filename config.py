import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:dxYASrceefsUkaVPorvmSaxxEvUvRnRo@junction.proxy.rlwy.net:56330/railway'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    POWER_BI_URL = os.getenv("POWER_BI_URL")