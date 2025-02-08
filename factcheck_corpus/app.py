from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy 
from flask_marshmallow import Marshmallow
import os


# Init app
app = Flask(__name__)
baseDir = os.path.abspath(os.path.dirname(__file__))

# Database Connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(baseDir, 'db.sqlite') 
# 'fact_checks://postgres:fact_checks@192.168.1.13/fact_check_collector'
app.config['SQLALCHEMY_TARCK_MODIFICATIONS'] = False

# Init db
db = SQLAlchemy(app)

# Init marshmallow
ma = Marshmallow(app)


# Product Class
class factCheckDB(db.Model):
    ids = db.Column(db.String, primary_key = True)
    source = db.Column(db.String)
    claimer = db.Column(db.String)

    def __init__(self, ids, source, claimer):
        self.ids = ids
        self.source = source
        self.claimer = claimer

# Fact Check Schema
class factCheckDBSchema(ma.Schema):
    class Meta:
        fields = ('ids', 'source', 'claimer')

# Init Schema
factCheck_DB = factCheckDBSchema()
factChecks_DB = factCheckDBSchema()

# Create a fact_checkDB
@app.route('/db', methods=['POST'])
def add_db():
    ids = request.json['ids']
    source = request.json['source']
    claimer = request.json['claimer']

    new_DB = factCheckDB(ids, source, claimer)

    db.session.add(new_DB)
    db.session.commit()

    return factCheckDBSchema.jsonify(new_DB)

@app.route('/', methods = ['GET'])
def index():
    return jsonify({'msg': 'Aye Hello!'})

# Run Server
if __name__ == "__main__":
    app.run(host="localhost", port=5698, debug = True)
