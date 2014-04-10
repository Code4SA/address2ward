import json
import psycopg2
from flask import Flask
from flask import Response
from flask import request
from flask import render_template
from flask import g
from config import configuration as config
#from convert import AddressConverter, Ward2006AddressConverter
from converters import converters

app = Flask(__name__)

class UnknownDatabaseException(Exception):
    pass

def get_connection(database):
    if not database in config["databases"]:
        raise UnknownDatabaseException("Could not find database: %s in configuration" % database)

    db_config = config["databases"][database]
    return psycopg2.connect(
        database=db_config["database"], user=db_config["db_user"],
        host=db_config["db_host"], password=db_config["db_password"]
    )

def get_db(database):
    if not hasattr(g, "_connections"):
        g._connections = {}

    if not database in g._connections:
        g._connections[database] = get_connection(database)
    return g._connections[database]

def get_converter(database):
    converter = getattr(g, '_converter', None)
    if converter is None:
        converter_class = converters[database]
        converter = g._converter = converter_class(get_db(database).cursor())
    return converter

@app.teardown_appcontext
def close_connection(exception):
    if hasattr(g, "_connections"):
        for db in g._connections.values():
            db.close()

@app.route("/wards/2006/", methods=["GET"])
@app.route("/", methods=["GET"])
def a2w():
    """
    addition parameters for address quality can be added
    e.g.
    http://.....?address=51+Main+Rd,Limpopo&remove_numbers
    
    options are:
    remove_numbers - strings that are all numbers
    remove_short_words - remove short tokens, the parameter given is the cut of size, e.g.

        http://.....?address=51+Main+Rd,Limpopo&remove_short_words=4 

    will remove all addresses where the address length is 4 letters or less
    
    """
    address = request.args.get("address")
    database = request.args.get("database", "wards_2006")
    
    params = dict(request.args)
    if "address" in params:
        del params["address"]

    if address:
        js = get_converter(database).convert(address, **params)
        js = js or {"error" : "address not found"}
        return Response(
            response=json.dumps(js, indent=4), status=200, mimetype="application/json"
        )
    else:
        return render_template("search.html")

if __name__ == "__main__":
    app.run(debug=True)
        
