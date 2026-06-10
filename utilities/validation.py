from functools import wraps
from flask import request, jsonify, g
from pydantic import ValidationError

def validate_schema(schema_class):
    """
    Decorator to validate JSON request bodies against a Pydantic schema.
    Injects the validated schema instance into flask.g.validated_data.
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            if not request.is_json:
                return jsonify({"error": "Request body must be JSON"}), 400
            try:
                data = request.get_json() or {}
                # Parse and validate using Pydantic
                g.validated_data = schema_class(**data)
            except ValidationError as e:
                # Format pydantic errors for front-end consumption
                formatted_errors = []
                for error in e.errors():
                    formatted_errors.append({
                        "field": ".".join(map(str, error["loc"])),
                        "message": error["msg"]
                    })
                return jsonify({"error": "Validation failed", "details": formatted_errors}), 400
            except Exception as e:
                return jsonify({"error": "Invalid JSON payload format"}), 400
            return f(*args, **kwargs)
        return wrapper
    return decorator
