import json
import psycopg2
from flask import Flask
from flask import Response
from flask import request
from flask import render_template
from flask import g
import config
from convert import AddressConverter

app = Flask(__name__)

def get_connection(database):
    return psycopg2.connect(
        database=config.database, user="wards",
        host="localhost", password="wards"
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
        converter = g._converter = AddressConverter(get_db(database).cursor())
    return converter

@app.teardown_appcontext
def close_connection(exception):
    if hasattr(g, "_connections"):
        for db in g._connections.values():
            db.close()

@app.route("/", methods=["GET"])
def a2w():
    address = request.args.get("address")
    database = request.args.get("address", config.database)
    
    if address:
        js = get_converter(database).convert(address)
        js = js or {"error" : "address not found"}
        return Response(
            response=json.dumps(js, indent=4), status=200, mimetype="application/json"
        )
    else:
        return render_template("search.html")

if __name__ == "__main__":
    conn = get_connection("wards_2006")
    try:
        converter = AddressConverter(conn.cursor())
        app.run(debug=True)
    finally:
        conn.close()
        
