from flask import Flask
from flask_pymongo import PyMongo

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'flask_api'
app.config['MONGO_URI'] = 'mongodb://flask:flask123@ds247121.mlab.com:47121/flask_api'

mongo = Pymongo(app) 	

@app.route('/add')
def add():
	user = mongo.db.users
	user.insert({'name': "allen"})
	return 'Added User!'

if __name__ == '__main__':
	app.run(debug=True)