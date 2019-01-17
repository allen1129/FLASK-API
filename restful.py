from flask import Flask
from flask_pymongo import PyMongo
from flask import jsonify 
from flask import request

app = Flask(__name__)

app.config['MONGO_DBNAME'] = 'flask_api'
app.config['MONGO_URI'] = 'mongodb://flask:flask123@ds247121.mlab.com:47121/flask_api'

mongo = PyMongo(app) 	



############################################
##	Merchants                             ##
##	Fields: (id, name, description, logo) ##
############################################

#get All Merchants
@app.route('/merchants', methods=['GET'])
def get_all_merchants():
	merchants = mongo.db.merchants
	data = []
	for q in merchants.find():
		data.append({"id": q['id'],"name" : q['name'] , "description" : q['description'] , "logo" : q['logo']})

	return jsonify({'code' : 0 , 'message' : "Success" , 'data' : data })

#find one merchant
@app.route('/merchants/<id>', methods=['GET'])
def get_merchant(id):
	merchants = mongo.db.merchants
	q = merchants.find_one({'id': id})
	data = {"id": q['id'],"name" : q['name'] , "description" : q['description'] , "logo" : q['logo']}
	return jsonify({'code' : 0 , 'message' : "Success" , 'data' : data })

#save merchants via post
@app.route('/merchants', methods=['POST'])
def add_merchants():
	merchants = mongo.db.merchants
	data = request.json
	merchants.insert(data)
	return jsonify({'code' : 0 , 'message' : "saved"})




############################################
##	Product                               ##
##	Fields: (id, name, price, logo) 	  ##
############################################

#get All Product
@app.route('/products', methods=['GET'])
def get_all_products():
	table = mongo.db.products
	data = []
	for q in table.find():
		data.append({"id": q['id'],"name" : q['name'] , "price" : q['price'] , "logo" : q['logo']})

	return jsonify({'code' : 0 , 'message' : "Success" , 'data' : data })

#find one Product
@app.route('/products/<id>', methods=['GET'])
def get_product(id):
	table = mongo.db.merchants
	q = table.find_one({'id': id})
	data = {"id": q['id'],"name" : q['name'] , "price" : q['price'] , "logo" : q['logo']}
	return jsonify({'code' : 0 , 'message' : "Success" , 'data' : data })

#save Product via post
@app.route('/products', methods=['POST'])
def add_product():
	table = mongo.db.merchants
	data = request.json
	table.insert(data)
	return jsonify({'code' : 0 , 'message' : "saved"})


############################################
##	Client                                ##
##	Fields: (id, name, email)        	  ##
############################################

#get All Client
@app.route('/clients', methods=['GET'])
def get_all_client():
	table = mongo.db.clients
	data = []
	for q in table.find():
		data.append({"id": q['id'],"name" : q['name'] , "email" : q['email']})

	return jsonify({'code' : 0 , 'message' : "Success" , 'data' : data })

#find one Client
@app.route('/clients/<id>', methods=['GET'])
def get_client(id):
	table = mongo.db.clients
	q = table.find_one({'id': id})
	data = {"id": q['id'],"name" : q['name'] , "email" : q['email'] }
	return jsonify({'code' : 0 , 'message' : "Success" , 'data' : data })

#save Client via post
@app.route('/clients', methods=['POST'])
def add_client():
	table = mongo.db.clients
	data = request.json
	table.insert(data)
	return jsonify({'code' : 0 , 'message' : "saved"})



######################################################################
##	Promo                                		   					##
##	Fields: (id, name, logo, start_date, end_date, status, user_id) ##
######################################################################

#get All Promo
@app.route('/promo', methods=['GET'])
def get_all_promo():
	table = mongo.db.promo
	data = []
	for q in table.find():
		data.append({"id": q['id'],
					"name" : q['name'] ,
					"logo" : q['logo'], 
					"start_date" : q['start_date'],
					"end_date" : q['end_date'],
					"status" : q['status'],
					"user_id" : q['user_id']
				})

	return jsonify({'code' : 0 , 'message' : "Success" , 'data' : data })

#find one Promo
@app.route('/promo/<id>', methods=['GET'])
def get_promo(id):
	table = mongo.db.promo
	q = table.find_one({'id': id})
	data = {"id": q['id'],
				"name" : q['name'] ,
				"logo" : q['logo'], 
				"start_date" : q['start_date'],
				"end_date" : q['end_date'],
				"status" : q['status'],
				"user_id" : q['user_id']
			}
	return jsonify({'code' : 0 , 'message' : "Success" , 'data' : data })

#save Promo via post
@app.route('/clients', methods=['POST'])
def add_promo():
	table = mongo.db.promo
	data = request.json
	table.insert(data)
	return jsonify({'code' : 0 , 'message' : "saved"})


if __name__ == '__main__':
	app.run(debug=True)