import hmac
from fastapi import Request
from app.config import ADMIN_USERNAME, ADMIN_PASSWORD

def valid_admin(username,password):
    return bool(ADMIN_USERNAME and ADMIN_PASSWORD) and hmac.compare_digest(username,ADMIN_USERNAME) and hmac.compare_digest(password,ADMIN_PASSWORD)

def is_logged_in(request:Request):
    return request.cookies.get("mr_rean_admin") == "1"
