from flask_restful import Api

from app  import flaskAppInstance
from .Task import Task

restServr = Api(flaskAppInstance)

restServr.add_resource(Task, "/api/task")