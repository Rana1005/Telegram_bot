from flask_swagger_ui import get_swaggerui_blueprint


SWAGGER_URL = '/swagger'  # URL for exposing Swagger UI (without trailing '/')

# API_URL =  "https://py-telegramjoshua.mobiloitte.io/static/swagger.json"
API_URL =  "http://172.16.6.43:8001/static/swagger.json"

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,  # Swagger UI static files will be mapped to '{SWAGGER_URL}/dist/'
    API_URL,
    config = {  # Swagger UI config overrides
        'app_name': "app config"
    },
)