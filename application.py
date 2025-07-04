from flask import Flask, request, jsonify, redirect
from flask_cors import CORS
import yaml
from bson import json_util
from haversine import haversine, Unit
from pymongo import MongoClient
from dotenv import load_dotenv
import uuid     
import os

load_dotenv()

application = Flask(__name__)
application.config['YAML_AS_TEXT'] = True
application.debug = os.environ.get("FLASK_DEBUG", False)
CORS(application)

MONGO_URI = os.environ.get("MONGODB_URI")

mongo_client = MongoClient(MONGO_URI, ssl=True)
db = mongo_client[os.environ.get("DATABASE_NAME")]

@application.route('/')
def home():
    return "Secure, You are in GPI Backend !!"

unique_id = str(uuid.uuid4())
@application.route('/generate-link/<string:admin_id>', methods=['GET'])
def generate_link(admin_id):
    unique_link = f"https://gpi.software/student-form/{admin_id}/{unique_id}"
    return {'link': unique_link}

@application.route('/class-data', methods=['POST', 'GET'])
def classdata():
    if request.method == 'POST':
        data = yaml.safe_load(request.data)

        classData = db.class_data
        classData.insert_one(data)

        return {'Output': 'Data inserted successfully'}
    else:
        return {'Error': 'No data provided'}, 400

@application.route('/student-data/<string:admin_id>/<string:provided_id>', methods=['POST'])
def studentdata(admin_id, provided_id):
    if provided_id == unique_id:
        if request.method == 'POST':
            data = yaml.safe_load(request.data)

            class_data = db.class_data
            class_info = class_data.find_one()

            if class_info:
                radius = float(class_info['radius'])

                admin_coord = (class_info['latitude'], class_info['longitude'])
                user_coord = (data['latitude'], data['longitude'])

                distance = float(haversine(admin_coord, user_coord, unit=Unit.METERS))

                data['present'] = distance < radius

                studentData = db.student_data
                studentData.insert_one(data)
                return {'Output': 'Data inserted successfully'}
            else:
                return {'Error': 'No class data found'}, 400
        else:
            return {'Error': 'No data provided'}, 400
    else:
        return {'Error': 'Invalid Unique ID'}, 400

@application.route('/getClassData', methods=['GET'])
def GetClassData():
    class_data = db.class_data
    class_info = class_data.find_one()

    if class_info:
        class_info['_id'] = str(class_info['_id'])
        print(class_info)
        return jsonify(class_info)
    else:
        return jsonify({})


@application.route('/getStudentData', methods=['GET'])
def GetStudentData():
    student_data = db.student_data
    student_info = student_data.find()

    if student_info:
        data = [item for item in student_info]

        for item in data:
            item['_id'] = str(item['_id'])

        return jsonify(data)
    else :
        return jsonify([])

if __name__ == "__main__":
    application.run()
