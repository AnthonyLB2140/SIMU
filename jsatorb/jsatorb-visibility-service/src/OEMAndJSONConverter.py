# Original author: ISAE, continued by CS Group

import json
from jinja2 import Environment, PackageLoader, select_autoescape, Template, FileSystemLoader
from datetime import datetime
from PropagationTimeSettings import PropagationTimeSettings
import copy

class OEMAndJSONConverter:
    """
    This class permits to convert an a JSON File into an OEM text file
    """

    def __init__(self, PropagationResultList):
        """Take a propagation result list to convert it intoo the right format"""
        self.listData = PropagationResultList


        # with open('./template.txt') as f:
        #     print(type(f.read()))
        #     self.oemTemplate = f.read()
        #

        file_loader = FileSystemLoader('templates')
        env = Environment(loader=file_loader)
        self.oemTemplate = env.get_template('template.txt')


    def getJSON(self):
        """
        Generate and return the JSON data related to the data result use in the constructor
        Not used in the current version of JSatOrb
        """

        result = []
        for key, value in self.listData.items():
            jsonObj = {}
            jsonObj["meta"] = {}
            jsonObj["meta"]["OBJECT_NAME"] = key
            jsonObj["meta"]["OBJECT_ID"] = key
            jsonObj["meta"]["CENTER_NAME"] = "Earth"
            jsonObj["meta"]["REF_FRAME"] = "EME2000"
            jsonObj["meta"]["TIME_SYSTEM"] = "UTC"
            jsonObj["meta"]["START_TIME"] = value[0]["epoch"]
            jsonObj["meta"]["USEABLE_START_TIME"] = value[0]["epoch"]
            jsonObj["meta"]["USEABLE_STOP_TIME"] = value[-1]["epoch"]
            jsonObj["meta"]["STOP_TIME"] = value[-1]["epoch"]
            jsonObj["meta"]["INTERPOLATION"] = "lagrange"
            jsonObj["meta"]["INTERPOLATION_DEGREE"] = 5
            jsonObj["data"] = value
            result.append(jsonObj)

        return result

    def getOEM(self, centralBody):
        """
        Get the OEM data related to the data result use in the constructor
        :return:
        """
        oemTemplate = None
        with open('./templates/template.txt') as f:
            oemTemplate = f.read()

        output = Template(oemTemplate)
        timeNow = datetime.utcnow().isoformat()
        centralBody = centralBody.lower().capitalize()
        return output.render(timeNow=timeNow, celestialBody=centralBody, satellitesResult=self.listData)


if __name__ == "__main__":
    from pprint import pprint
    """ Rien pour le moment """
    data = {"monJolieSat#1": [{"epoch": "2011-12-02T00:43:45.000", "x": -962530.5145265183, "y": 5744056.407420587, "z": 4127824.992798455, "vx": 4214.895489033509,"vy": 548.6789, "vz": 5344.292081959501}]}
    test = OEMAndJSONConverter(data)
    pprint(test.getOEM())
    pprint(test.getJSON())

    # oemTemplate = None
    # with open('./templates/template.txt') as f:
    #     oemTemplate = f.read()
    #
    # output = Template(oemTemplate)
    # timeNow = str(datetime.utcnow())
    # print(output.render(timeNow=timeNow, satellitesResult=data))
