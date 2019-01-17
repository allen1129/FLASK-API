import datetime
import functools
import uuid
import os
import base64

from bson.objectid import ObjectId
from flask import (
    Flask, flash, render_template, session, request, redirect, url_for, jsonify, send_file)
from pymodm.errors import ValidationError
from pymongo.errors import DuplicateKeyError

from flask_jwt_extended import (
    JWTManager, jwt_required, create_access_token,
    get_jwt_identity, verify_jwt_in_request, get_jwt_claims
)

from my_models import User, Product, Order, ProductOrder, Promo, UserPromo

# Secret key used to encrypt session cookies.
SECRET_KEY = str(uuid.uuid4())
# Folder where uploaded images will be stored
UPLOAD_FOLDER = os.path.basename('uploads')

app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = 'super-secret'  # Change this!
jwt = JWTManager(app)

app.secret_key = SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def human_date(value, format="%B %d at %I'%M %p"):
    """Format a datetime object to be human-readable in a template."""
    return value.strftime(format)
app.jinja_env.filters['human_date'] = human_date
app.config['HUMAN_DATE'] = str(datetime.datetime.now())

def merchant_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()

        if claims['user_type'] != 'MERCHANT':
            return jsonify(msg='not allowed'), 403
        else:
            return fn(*args, **kwargs)
    return wrapper

def client_required(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        claims = get_jwt_claims()

        if claims['user_type'] != 'CLIENT':
            return jsonify(msg='not allowed'), 403
        else:
            return fn(*args, **kwargs)
    return wrapper

@jwt.user_claims_loader
def add_claims_to_access_token(identity):
    return identity

@app.route('/login', methods=['POST'])
def login():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    username = request.json.get('email', None)
    password = request.json.get('password', None)

    if not username:
        return jsonify({"status": "FALSE", "msg": "Missing email parameter"}), 400
    if not password:
        return jsonify({"status": "FALSE", "msg": "Missing password parameter"}), 400

    # if username != 'test' or password != 'test':
    #     return jsonify({"msg": "Bad username or parameter assword"}), 401
    try:
        user = User.objects.get({"_id": username})
    except User.DoesNotExist:
        return jsonify({"status": "FALSE", "msg": "No existing record found"}), 401
    
    if user.verify_password(user.password, password):
        # Identity can be any data that is json serializable
        access_token = create_access_token(identity={"email": username, "user_type": user.user_type})
        return jsonify(access_token=access_token, status="TRUE"), 200
    else:
        return jsonify({"status": "FALSE","msg": "Invalid credentials"}), 401

# Protect a view with jwt_required, which requires a valid access token
# in the request to access.
@app.route('/protected', methods=['GET'])
@jwt_required
def protected():
    # Access the identity of the current user with get_jwt_identity
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@app.route('/users', methods=['GET'])
def get_all_users():
    try:
        data = []

        objects = User.objects.all()

        for object in objects:
            data.append({
                'email': object.email
            })

        return jsonify(status="TRUE", users=data)

    except Product.DoesNotExist:
        return jsonify(status="FALSE", msg="No record found.")


@app.route('/registration', methods=['POST'])
def new_user():
    try:
        if not request.is_json:
            return jsonify({"msg": "Missing JSON in request"}), 400
        # Note: real applications should handle user registration more
        # securely than this.
        user = User(email=request.json['email'],
             # Use `force_insert` so that we get a DuplicateKeyError if
             # another user already exists with the same email address.
             # Without this option, we will update (replace) the user with
             # the same id (email).
             user_type=request.json['user_type'])

        user.hash_password(request.json['password'])
        user.save(force_insert=True)

        data = {
            'email': user.email,
            'user_type': user.user_type
        }
        print "1"
        if request.json['user_type'] == 'MERCHANT':
            print "MERCHANT"
            url = convert_and_save(request.json['image'])
            print url
            user.image_url=url
            user.save()

            data['image'] = convert_and_send(user.image_url)

        api_response = jsonify({"status":"TRUE", "data" : data})

        return api_response
    except ValidationError as ve:
        return jsonify({"status": "FALSE",'errors':ve.message})
    except DuplicateKeyError:
        # Email address must be unique.
        return jsonify({"status": "FALSE",'errors':{'email': 'There is already a user with that email address.'}})

@app.route('/products', methods=['POST'])
@merchant_required
def create_product():
    try:
        if not request.is_json:
            return jsonify({"msg": "Missing JSON in request"}), 400

        slugify = request.json['name'].lower()

        #This function is working only takes a lot of RAM in postman api testing
        url = convert_and_save(request.json['image'])
        
        product = Product(name=request.json['name'],
            price=request.json['price'],
            image_url=url,
            slug=slugify.replace(" ", "-")).save()

        api_response = jsonify({"status":"TRUE", "data" : {
            'name': product.name,
            'price': product.price,
            'image': convert_and_send(product.image_url)
        }})

        return api_response
    except ValidationError as exc:
        return jsonify({"status": "FALSE",'errors':exc.message})

@app.route('/products', methods=['GET'])
@jwt_required
def get_all_products():
    try:
        data = []

        products = Product.objects.all()

        for product in products:
            data.append({
                'name': product.name,
                'price': product.price,
                'image': convert_and_send(product.image_url),
                'product_id': product.slug
            })

        return jsonify(status="TRUE", products=data)

    except Product.DoesNotExist:
        return jsonify(status="FALSE", msg="No record found.")

@app.route('/products/<product_id>', methods=['GET'])
@jwt_required
def get_product(product_id):
    try:
        product = Product.objects.get({'_id': product_id})

        data = {
            'name': product.name,
            'price': product.price,
            'image': convert_and_send(product.image_url),
            'product_id': product.slug
        }

        return jsonify(status="TRUE", product=data)
    except Product.DoesNotExist:
        return render_template('404.html'), 404

@app.route('/promos', methods=['POST'])
@merchant_required
def create_promo():
    try:
        url = convert_and_save(request.json['image'])

        slugify = request.json['name'].lower()

        promo = Promo(name=request.json['name'],
             start_date=request.json['start_date'],
             end_date=request.json['end_date'],
             image_url=url,
             slug=slugify.replace(" ", "-")).save()

        data = {
            'id': promo.slug,
            'name': promo.name,
            'start_date': promo.start_date,
            'end_date': promo.end_date,
            'image': convert_and_send(promo.image_url)
        }

        return jsonify(status="TRUE", data=data)
    except ValidationError as exc:
        return jsonify({"status": "FALSE",'errors':exc.message})

#Get all promos that still available
@app.route('/promos', methods=['GET'])
@jwt_required
def get_all_promos():
    try:
        data = []

        current_date = datetime.datetime.now().strftime('%Y-%m-%d')

        promos = Promo.objects.all()

        for promo in promos:
            start_date = promo.start_date.strftime('%Y-%m-%d')
            end_date = promo.end_date.strftime('%Y-%m-%d')

            if current_date >= start_date and current_date <= end_date:
                data.append({
                    'id': promo.slug,
                    'name': promo.name,
                    'start_date': promo.start_date,
                    'end_date': promo.end_date,
                    'image': convert_and_send(promo.image_url)
                })

        return jsonify(status="TRUE", promos=data)

    except Promo.DoesNotExist:
        return jsonify(status="FALSE", msg="No record found.")

@app.route('/promos/avail', methods=['POST'])
@client_required
def avail_promo():
    try:
        if not request.is_json:
            return jsonify({"msg": "Missing JSON in request"}), 400

        claims = get_jwt_claims()
        data = []

        current_date = datetime.datetime.now().strftime('%Y-%m-%d')

        user = User.objects.raw({'_id': claims['email']}).first()
        promo = Promo.objects.raw({'_id': request.json['promo_id']}).first()

        data = {
            'id': promo.slug,
            'name': promo.name,
            'start_date': promo.start_date,
            'end_date': promo.end_date,
            'image': convert_and_send(promo.image_url)
        }

        start_date = promo.start_date.strftime('%Y-%m-%d')
        end_date = promo.end_date.strftime('%Y-%m-%d')

        if current_date >= start_date and current_date <= end_date:

            if not any(d.promo_id == request.json['promo_id'] for d in user.user_promos):
                print 'Watch out!' 
                user_promo = UserPromo(
                    promo_id=request.json['promo_id'],
                    status="availed"
                )

                user.user_promos.append(user_promo)

                try:
                    user.save()
                except ValidationError as e:
                    user.user_promo.pop()
                    promo_errors = e.message['user_promo'][-1]

                    return jsonify(status="FALSE", errors=promo_errors)

                return jsonify(status="TRUE", promo=data, msg="You have successfully availed the %s promo" %promo.name)
            else:
                return jsonify(status="FALSE", msg="You already availed this promo")
        return jsonify(status="TRUE", promo=data, msg="The %s promo is alread expired or not yet available" %promo.name)
        
    except Promo.DoesNotExist:
        return jsonify(status="FALSE", msg="Invalid promo.")

@app.route('/promos/redeem', methods=['POST'])
@client_required
def redeem_promo():
    try:
        if not request.is_json:
            return jsonify({"msg": "Missing JSON in request"}), 400

        claims = get_jwt_claims()
        data = []

        current_date = datetime.datetime.now().strftime('%Y-%m-%d')

        user = User.objects.get({'_id': claims['email'], "user_promos":{"$elemMatch":{"promo_id":request.json['promo_id']}}})#.first()
        #dump(user)
        promo = Promo.objects.get({'_id': request.json['promo_id']})
       # print user
        #user.user_promos.status("redeemed").save()

        data = {
            'id': promo.slug,
            'name': promo.name,
            'start_date': promo.start_date,
            'end_date': promo.end_date,
            'image': convert_and_send(promo.image_url)
        }

        end_date = promo.end_date.strftime('%Y-%m-%d')
        ctr = 0
        if current_date <= end_date:
            for d in user.user_promos:
                if d.promo_id == request.json['promo_id'] :  
                    user.user_promos[ctr].status  = "redeemed"
                    try:
                        user.save()
                    except ValidationError as e:
                        user.user_promo.pop()
                        promo_errors = e.message['user_promo'][-1]

                        return jsonify(status="FALSE", errors=promo_errors)
                ctr += 1
            #else:
             #   return jsonify(status="FALSE", msg="You cannot redeem this promo.")

        return jsonify(status="TRUE", promo=data, msg="You have successfully redeemed the %s promo" %promo.name)
    except  User.DoesNotExist:  
        return jsonify(status = "FALSE", msg="Promo was not availed by the user")
    except Promo.DoesNotExist:
        return jsonify(status="FALSE", msg="Invalid promo.")

@app.route('/order', methods=['POST'])
@client_required
def order():
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    product_id = request.json['product_id']
    claims = get_jwt_claims()

    try:
        product = Product.objects.get({'_id': product_id})

        data = {
            'name': product.name,
            'price': product.price,
            'image': convert_and_send(product.image_url),
            'product_id': product.slug
        }
    except Product.DoesNotExist:
        return jsonify(status="FALSE", msg='No product with id: %s' % product_id)

    order = Order(
        client_id=claims['email'],
        date=datetime.datetime.now(),
        product_id=request.json['product_id']).save()

    product_order = ProductOrder(
        client_id=claims['email'],
        date=datetime.datetime.now(),
        product_id=request.json['product_id'])
    product.order.append(product_order)
    try:
        product.save()
    except ValidationError as e:
        product.order.pop()
        purchase_errors = e.message['order'][-1]

        return jsonify(status="FALSE", product=data, errors=purchase_errors)

    return jsonify(status="TRUE", msg="You have successfully purchased the item: %s" %product.name, product=data)

@app.route('/orders', methods=['GET'])
@jwt_required
def get_all_orders():
    claims = get_jwt_claims()
    try:
        data = []

        orders = Order.objects.raw({'client_id':claims['email']})

        for order in orders:
            try:
                product = Product.objects.raw({"_id": order.product_id}).first()
            except Product.DoesNotExist:
                return jsonify(status="FALSE", msg="Error: Product does not exist")

            data.append({
                'product_name': product.name,
                'price': product.price,
                'image': convert_and_send(product.image_url),
                'product_id': product.slug,
                'date': order.date
            })

        return jsonify(status="TRUE", orders=data)

    except Order.DoesNotExist:
        return jsonify(status="FALSE", msg="No records found")

#This function is working only takes a lot of RAM in postman api testing (working laptop)    
def convert_and_save(b64_string):
    path = app.config['UPLOAD_FOLDER']
    filename = str(uuid.uuid4()) + "-" + app.config['HUMAN_DATE'] + '.png'
    filepath = path + '/' + filename.replace(":","'")
    with open(filepath, "wb") as fh:
        fh.write(base64.b64decode(b64_string))

    return filepath

def convert_and_send(image_file):
    with open(image_file, "rb") as imageFile:
        str = base64.b64encode(imageFile.read())

    return str

def dump(obj):
   for attr in dir(obj):
       if hasattr( obj, attr ):
           print( "obj.%s = %s" % (attr, getattr(obj, attr)))

def main():
    app.run(debug=True)


if __name__ == '__main__':
    main()
