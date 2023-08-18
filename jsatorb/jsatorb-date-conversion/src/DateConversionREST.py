import bottle
from bottle import request, response
import json

from DateConversion import HAL_DateConversion

app = application = bottle.default_app()

# the decorator
def enable_cors(fn):
    def _enable_cors(*args, **kwargs):
        # set CORS headers
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, X-CSRF-Token'

        if bottle.request.method != 'OPTIONS':
            # actual request; reply with the actual response
            return fn(*args, **kwargs)
    return _enable_cors

@app.route('/dateconversion', method=['OPTIONS', 'POST'])
@enable_cors
def DateConversionREST():
    response.content_type = 'application/json'
    data = request.json
    print(json.dumps(data))
    header = data['header']
    dateToConvert = header['dateToConvert']
    targetFormat = header['targetFormat']

    newDate = HAL_DateConversion(dateToConvert, targetFormat)

    # Return json with converted date in 'dateConverted'
    return json.dumps(newDate.getDateTime())

if __name__ == '__main__':
    bottle.run(host = '127.0.0.1', port = 8000)