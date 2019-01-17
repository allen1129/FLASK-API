from flask_restful import Resource
import logging as logger

class Task(Resource):

	def get(self):
		logger.debug("Inside get method")
		return {"message": "inside get method"}, 200

	def post(self):
		logger.debug("Inside post method")
		return {"message": "inside post method"}, 200

	def put(self):
		logger.debug("Inside put method")
		return {"message": "inside put method"}, 200

	def delete(self):
		logger.debug("Inside delete method")
		return {"message": "inside delete method"}, 200