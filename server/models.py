from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import MetaData
from sqlalchemy.ext.associationproxy import association_proxy
from marshmallow import Schema, fields


# Naming convention helps Flask-Migrate generate clean FK names
metadata = MetaData(naming_convention={
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
})

db = SQLAlchemy(metadata=metadata)


# ======================================================
# CUSTOMER MODEL
# ======================================================
class Customer(db.Model):
    __tablename__ = 'customers'

    # Primary key (unique identifier)
    id = db.Column(db.Integer, primary_key=True)

    # Simple column storing customer name
    name = db.Column(db.String)

    # ---------------------------
    # RELATIONSHIP:
    # One customer -> many reviews
    #
    # back_populates MUST match the attribute name
    # defined on Review.customer
    #
    # Think of this as:
    # "Give me all reviews written by this customer"
    # ---------------------------
    reviews = db.relationship('Review', back_populates='customer')

    # ---------------------------
    # ASSOCIATION PROXY:
    #
    # Instead of doing:
    # [review.item for review in customer.reviews]
    #
    # we can just do:
    # customer.items
    #
    # This DOES NOT create a table column —
    # it just provides a shortcut to related objects.
    # ---------------------------
    items = association_proxy('reviews', 'item')

    def __repr__(self):
        return f'<Customer {self.id}, {self.name}>'


# ======================================================
# ITEM MODEL
# ======================================================
class Item(db.Model):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    price = db.Column(db.Float)

    # ---------------------------
    # RELATIONSHIP:
    # One item -> many reviews
    #
    # "Give me all reviews written about this item"
    # ---------------------------
    reviews = db.relationship('Review', back_populates='item')

    def __repr__(self):
        return f'<Item {self.id}, {self.name}, {self.price}>'


# ======================================================
# REVIEW MODEL (JOIN TABLE)
# ======================================================
class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)

    # Text content of the review
    comment = db.Column(db.String)

    # ---------------------------
    # FOREIGN KEYS
    #
    # A review belongs to ONE customer
    # A review belongs to ONE item
    # ---------------------------
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))

    # ---------------------------
    # RELATIONSHIPS BACK TO MODELS
    #
    # These MUST mirror the relationships
    # defined in Customer and Item.
    #
    # back_populates connects BOTH SIDES
    # so SQLAlchemy keeps them synced.
    # ---------------------------
    customer = db.relationship('Customer', back_populates='reviews')
    item = db.relationship('Item', back_populates='reviews')

    def __repr__(self):
        return f'<Review {self.id}, {self.comment}>'


# ======================================================
# MARSHMALLOW SCHEMAS (SERIALIZATION)
# ======================================================

# BIG IDEA:
# Models = how data is stored
# Schemas = how data is converted into JSON/dicts


# ---------------------------
# REVIEW SCHEMA
#
# When serializing a review,
# include customer + item info.
#
# BUT exclude their "reviews"
# to avoid infinite recursion:
#
# review -> customer -> reviews -> review -> ...
# ---------------------------
class ReviewSchema(Schema):
    id = fields.Int()
    comment = fields.Str()

    customer = fields.Nested(
        lambda: CustomerSchema(exclude=('reviews',))
    )

    item = fields.Nested(
        lambda: ItemSchema(exclude=('reviews',))
    )


# ---------------------------
# CUSTOMER SCHEMA
#
# Include reviews,
# but remove the nested customer
# from each review to avoid loops.
# ---------------------------
class CustomerSchema(Schema):
    id = fields.Int()
    name = fields.Str()

    reviews = fields.Nested(
        ReviewSchema(exclude=('customer',)),
        many=True
    )


# ---------------------------
# ITEM SCHEMA
#
# Same logic:
# Include reviews,
# but exclude nested item inside review.
# ---------------------------
class ItemSchema(Schema):
    id = fields.Int()
    name = fields.Str()
    price = fields.Float()

    reviews = fields.Nested(
        ReviewSchema(exclude=('item',)),
        many=True
    )
