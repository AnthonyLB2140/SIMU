import bottle
from bottle import request, response
from MissionAnalysis import HAL_MissionAnalysis
import json

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

@app.route('/propagation/satellites', method=['OPTIONS','POST'])
@enable_cors
def satelliteJSON():
    response.content_type = 'application/json'
    data = request.json
    print(json.dumps(data))
    header = data['header']
    satellites = data['satellites']
    newMission = HAL_MissionAnalysis(header['step'], header['duration'])
    if 'timeStart' in header:
        newMission.setStartTime(header['timeStart'])

    for sat in  satellites:
        newMission.addSatellite(sat)

    newMission.propagate()
    return json.dumps(newMission.getJSONEphemerids())

@app.route('/propagation/visibility', method=['OPTIONS', 'POST'])
@enable_cors
def satelliteOEM():
    response.content_type = 'application/json'
    data = request.json
    header = data['header']
    satellites = data['satellites']
    groundStations = data['groundStations']
    newMission = HAL_MissionAnalysis(header['step'], header['duration'])
    if 'timeStart' in header:
        newMission.setStartTime(header['timeStart'])

    for sat in  satellites:
        newMission.addSatellite(sat)

    for gs in groundStations:
        newMission.addGroundStation(gs)

    newMission.propagate()
    return json.dumps(newMission.getVisibility())


if __name__ == '__main__':
    bottle.run(host = '127.0.0.1', port = 8000)