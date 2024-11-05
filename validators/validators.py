from flask import request, jsonify
from functools import wraps

def jwt_token_required(func):
    """
    Checks if token was given in request, requires "token" field
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "token" not in request.get_json():
            return jsonify({"message": "Token required"}), 401
        return func(*args, **kwargs)  # Передаем все аргументы в оригинальную функцию
    return wrapper