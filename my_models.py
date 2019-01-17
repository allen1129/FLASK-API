from pymodm import MongoModel, EmbeddedMongoModel, fields, connect

import uuid
import hashlib

# Establish a connection to the database.
connect('mongodb://flask:flask123@ds247121.mlab.com:47121/flask_api')

class UserPromo(EmbeddedMongoModel):
    promo_id = fields.CharField(required=True)
    status = fields.CharField(required=True)

class User(MongoModel):
    # Make all these fields required, so that if we try to save a User instance
    # that lacks one of these fields, we'll get a ValidationError, which we can
    # catch and render as an error on a form.
    #
    # Use the email as the "primary key" (will be stored as `_id` in MongoDB).
    email = fields.EmailField(primary_key=True, required=True)
    user_type = fields.CharField(required=True)
    image_url = fields.CharField(blank=True)
    # `password` here will be stored in plain text! We do this for simplicity of
    # the example, but this is not a good idea in general. A real authentication
    # system should only store hashed passwords, and queries for a matching
    # user/password will need to hash the password portion before of the query.
    password = fields.CharField(required=True)
    user_promos = fields.EmbeddedDocumentListField(UserPromo)

    def hash_password(self, password_input):
        salt = uuid.uuid4().hex
        self.password = hashlib.sha256(salt.encode() + password_input.encode()).hexdigest() + ':' + salt

    def verify_password(self, hashed_password, user_password):
        password, salt = hashed_password.split(':')
        return password == hashlib.sha256(salt.encode() + user_password.encode()).hexdigest()


# This is an EmbeddedMongoModel, which means that it will be stored *inside*
# another document (i.e. a Post), rather than getting its own collection. This
# makes it very easy to retrieve all comments with a Post, but we might consider
# breaking out Comment into its own top-level MongoModel if we were expecting to
# have very many comments for every Post.
class ProductOrder(EmbeddedMongoModel):
    # For comments, we just want an email. We don't require signup like we do
    # for a Post, which has an 'author' field that is a ReferenceField to User.
    # Again, we make all fields required so that we get a ValidationError if we
    # try to save a Comment instance that lacks one of these fields. We can
    # catch this error and render it in a form, telling the user that one or
    # more fields still need to be filled.
    client_id = fields.EmailField(required=True)
    product_id = fields.CharField(required=True)
    date = fields.DateTimeField(required=True)

class Product(MongoModel):
    # We set "blank=False" so that values like the empty string (i.e. u'')
    # aren't considered valid. We want a real title.  As above, we also make
    # most fields required here.
    slug = fields.CharField(primary_key=True, required=True)
    name = fields.CharField(required=True, blank=False)
    price = fields.CharField(required=True, blank=False)
    image_url = fields.CharField(required=False)
    order = fields.EmbeddedDocumentListField(ProductOrder)

class Promo(MongoModel):
    # We set "blank=False" so that values like the empty string (i.e. u'')
    # aren't considered valid. We want a real title.  As above, we also make
    # most fields required here.
    slug = fields.CharField(primary_key=True, required=True)
    name = fields.CharField(required=True, blank=False)
    image_url = fields.CharField()
    start_date = fields.DateTimeField(required=True)
    end_date = fields.DateTimeField(required=True)

class Order(MongoModel):
    # For comments, we just want an email. We don't require signup like we do
    # for a Post, which has an 'author' field that is a ReferenceField to User.
    # Again, we make all fields required so that we get a ValidationError if we
    # try to save a Comment instance that lacks one of these fields. We can
    # catch this error and render it in a form, telling the user that one or
    # more fields still need to be filled.
    client_id = fields.EmailField(required=True)
    product_id = fields.CharField(required=True)
    date = fields.DateTimeField(required=True)

    @property
    def summary(self):
        """Return at most 100 characters of the body."""
        if len(self.body) > 100:
            return self.body[:97] + '...'
        return self.body
