from flask import Blueprint, jsonify

docs_bp = Blueprint("docs", __name__)

OPENAPI_SPEC = {
    "openapi": "3.0.0",
    "info": {
        "title": "Smart Keyboard Converter AI - API Documentation",
        "description": (
            "Interactive REST API documentation for Smart Keyboard Converter AI. "
            "Supports layout conversion, layout builder engine, public marketplace, "
            "conversion history, statistics, and JWT-in-cookie authentication."
        ),
        "version": "1.0.0"
    },
    "servers": [
        {
            "url": "/",
            "description": "Local/Relative Server Environment"
        }
    ],
    "paths": {
        "/api/auth/register": {
            "post": {
                "summary": "Register a new user",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "email": {"type": "string", "format": "email"},
                                    "password": {"type": "string", "minLength": 8}
                                },
                                "required": ["email", "password"]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {"description": "User created. Verification email sent."},
                    "400": {"description": "Validation error or user exists."}
                }
            }
        },
        "/api/auth/login": {
            "post": {
                "summary": "Authenticate user",
                "description": "Sets access and refresh tokens in secure HttpOnly cookies.",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "email": {"type": "string", "format": "email"},
                                    "password": {"type": "string"},
                                    "remember_me": {"type": "boolean", "default": False}
                                },
                                "required": ["email", "password"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Login successful. Cookies set."},
                    "401": {"description": "Invalid credentials."}
                }
            }
        },
        "/api/auth/logout": {
            "post": {
                "summary": "Signout user",
                "description": "Clears JWT cookies and invalidates session token JTI.",
                "responses": {
                    "200": {"description": "Logout successful."}
                }
            }
        },
        "/api/auth/refresh": {
            "post": {
                "summary": "Refresh access cookies",
                "description": "Validates refresh cookie and sets new access token cookie.",
                "responses": {
                    "200": {"description": "Token refreshed."},
                    "401": {"description": "Session revoked or expired."}
                }
            }
        },
        "/api/auth/verify-email": {
            "get": {
                "summary": "Verify email token",
                "parameters": [
                    {
                        "name": "token",
                        "in": "query",
                        "required": True,
                        "schema": {"type": "string"}
                    }
                ],
                "responses": {
                    "200": {"description": "Email verified successfully."},
                    "400": {"description": "Invalid/expired token."}
                }
            }
        },
        "/api/auth/reset-password/request": {
            "post": {
                "summary": "Request password reset email",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "email": {"type": "string", "format": "email"}
                                },
                                "required": ["email"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Reset instructions sent if email exists."}
                }
            }
        },
        "/api/auth/reset-password/confirm": {
            "post": {
                "summary": "Set new password via token",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "token": {"type": "string"},
                                    "new_password": {"type": "string", "minLength": 8}
                                },
                                "required": ["token", "new_password"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Password reset successfully."},
                    "400": {"description": "Invalid/expired token."}
                }
            }
        },
        "/api/auth/profile": {
            "get": {
                "summary": "Retrieve user profile details",
                "security": [{"cookieAuth": []}],
                "responses": {
                    "200": {"description": "Profile data retrieved."},
                    "401": {"description": "Unauthorized."}
                }
            },
            "put": {
                "summary": "Modify profile parameters",
                "security": [{"cookieAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "current_password": {"type": "string"},
                                    "new_password": {"type": "string"}
                                }
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Profile updated."},
                    "400": {"description": "Invalid passwords."},
                    "401": {"description": "Unauthorized."}
                }
            }
        },
        "/api/auth/ai-settings": {
            "put": {
                "summary": "Update user AI preferences",
                "security": [{"cookieAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "preferred_model": {"type": "string"},
                                    "temperature": {"type": "number", "minimum": 0, "maximum": 2},
                                    "prompt_prefix": {"type": "string"}
                                },
                                "required": ["preferred_model", "temperature"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Settings updated."}
                }
            }
        },
        "/api/auth/stats": {
            "get": {
                "summary": "Fetch usage stats",
                "security": [{"cookieAuth": []}],
                "responses": {
                    "200": {"description": "Usage numbers returned."}
                }
            }
        },
        "/api/layouts": {
            "get": {
                "summary": "List custom user layouts",
                "security": [{"cookieAuth": []}],
                "responses": {
                    "200": {"description": "List returned."}
                }
            },
            "post": {
                "summary": "Create new custom mapping layout",
                "security": [{"cookieAuth": []}],
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "language": {"type": "string"},
                                    "mapping": {"type": "object", "additionalProperties": {"type": "string"}},
                                    "direction": {"type": "string", "enum": ["ltr", "rtl"]}
                                },
                                "required": ["name", "language", "mapping"]
                            }
                        }
                    }
                },
                "responses": {
                    "201": {"description": "Layout created."},
                    "400": {"description": "Validation failed."}
                }
            }
        },
        "/api/layouts/{id}": {
            "get": {
                "summary": "Retrieve specific layout",
                "security": [{"cookieAuth": []}],
                "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "Layout details."}}
            },
            "put": {
                "summary": "Modify layout details",
                "security": [{"cookieAuth": []}],
                "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "requestBody": {
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "name": {"type": "string"},
                                    "description": {"type": "string"},
                                    "mapping": {"type": "object"}
                                }
                            }
                        }
                    }
                },
                "responses": {"200": {"description": "Layout modified."}}
            },
            "delete": {
                "summary": "Delete custom layout",
                "security": [{"cookieAuth": []}],
                "parameters": [{"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}],
                "responses": {"200": {"description": "Deleted."}}
            }
        },
        "/api/converter/config": {
            "get": {
                "summary": "Query layout platform status",
                "description": "Indicates if AI enhancement modules are enabled/disabled on this deployment instance.",
                "responses": {"200": {"description": "Config metadata."}}
            }
        },
        "/api/converter/convert": {
            "post": {
                "summary": "Convert input text layout",
                "description": "Performs PC typewriter layout mapping translation, and optionally calls AI enhancement endpoints if mode > 1.",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string", "maxLength": 10000},
                                    "layout_id": {"type": "string"},
                                    "mode": {"type": "integer", "enum": [1, 2, 3, 4], "default": 1},
                                    "ai_settings": {
                                        "type": "object",
                                        "properties": {
                                            "preferred_model": {"type": "string"},
                                            "temperature": {"type": "number"}
                                        }
                                    }
                                },
                                "required": ["text", "layout_id"]
                            }
                        }
                    }
                },
                "responses": {
                    "200": {"description": "Conversions results."}
                }
            }
        },
        "/api/marketplace": {
            "get": {
                "summary": "Browse marketplace layouts",
                "parameters": [
                    {"name": "q", "in": "query", "schema": {"type": "string"}},
                    {"name": "language", "in": "query", "schema": {"type": "string"}},
                    {"name": "sort_by", "in": "query", "schema": {"type": "string", "enum": ["likes", "downloads", "newest"]}}
                ],
                "responses": {"200": {"description": "Browse results."}}
            }
        }
    },
    "components": {
        "securitySchemes": {
            "cookieAuth": {
                "type": "apiKey",
                "in": "cookie",
                "name": "access_token_cookie"
            }
        }
    }
}

@docs_bp.route("/openapi.json", methods=["GET"])
def get_spec():
    return jsonify(OPENAPI_SPEC)

@docs_bp.route("", methods=["GET"])
def render_swagger():
    return """
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="utf-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <title>Smart Keyboard Converter API - Documentation</title>
        <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui.css" />
        <style>
          html { box-sizing: border-box; overflow: -moz-scrollbars-vertical; overflow-y: scroll; }
          *, *:before, *:after { box-sizing: inherit; }
          body { margin:0; background: #fafafa; }
        </style>
      </head>
      <body>
        <div id="swagger-ui"></div>
        <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-bundle.js" charset="UTF-8"></script>
        <script src="https://unpkg.com/swagger-ui-dist@5.11.0/swagger-ui-standalone-preset.js" charset="UTF-8"></script>
        <script>
          window.onload = () => {
            window.ui = SwaggerUIBundle({
              url: '/api/docs/openapi.json',
              dom_id: '#swagger-ui',
              presets: [
                SwaggerUIBundle.presets.apis,
                SwaggerUIStandalonePreset
              ],
              layout: "StandaloneLayout"
            });
          };
        </script>
      </body>
    </html>
    """
