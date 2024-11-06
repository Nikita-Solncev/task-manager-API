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
        
        return func(*args, **kwargs)  
    return wrapper


# def check_register_data(func):
#     @wraps(func)
#     def wrapper():
#         data = request.get_json()
        
#         #chech if username is not a string
#         if isinstance(data.get("username"), str):
#             ...
#         else:
#             return jsonify({"message": "Username must be a string"}), 400
        
#         #chech lenght of username
#         if len(data.get("username")) > 50:
#             return jsonify({"message": "Username is too long, must be less than 50 symbols"}), 400
        
#         #check is username written only with latin 