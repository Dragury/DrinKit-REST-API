from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from flask_mysqldb import MySQL
from datetime import datetime, timedelta
import string, random, sys

app = Flask(__name__)
api = Api(app)
app.config['MYSQL_DB'] = "drinKit"
app.config['MYSQL_HOST'] = "127.0.0.1"
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['MYSQL_USER'] = sys.argv[1]
app.config['MYSQL_PASSWORD'] = sys.argv[2]
mysql = MySQL(app)


class Authenticate(Resource):
    def get(self, auth=None):
        if auth is None:
            return jsonify(None)
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM Auth WHERE CODE=%s", [auth])
        res = cursor.fetchone()
        if res is not None:
            access_time = datetime.now()
            if res['Expiry'] < access_time:
                query = "DELETE FROM Auth WHERE CODE=%s"
                cursor.execute(query, [auth])
                auth = None
            else:
                query = "UPDATE Auth SET Expiry=%s WHERE CODE=%s"
                cursor.execute(query, [
                    "{:%Y-%m-%d %H:%M:%S}".format(access_time + timedelta(hours=1)),
                    auth
                ])
            mysql.connection.commit()
            return jsonify(auth)
        return jsonify(None)

    def post(self, auth=None):
        if request.form['USER'] == app.config['MYSQL_USER'] and request.form['PASS'] == app.config['MYSQL_PASSWORD']:
            cursor = mysql.connection.cursor()
            access_time = datetime.now()
            print('{:%Y%M%S%d%H%m}'.format(access_time))
            key = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(50))
            cursor.execute("INSERT INTO Auth(CODE,Expiry) VALUES (%s,%s)", [
                key,
                "{:%Y-%m-%d %H:%M:%S}".format(access_time + timedelta(hours=1))
            ])
            mysql.connection.commit()
            return jsonify(key)
        return None, 403


api.add_resource(Authenticate, *["/auth", "/auth/<string:auth>"])


class Drink(Resource):
    def get(self, id=None):
        cursor = mysql.connection.cursor()
        if id is None:
            cursor.execute("SELECT * FROM Drinks")
            res = cursor.fetchall()
            return jsonify(res)
        else:
            id = int(id)
            cursor.execute("SELECT * FROM Drinks WHERE ID=%s", [id])
            return jsonify(cursor.fetchone())


api.add_resource(Drink, *["/drink", "/drink/<int:id>"])


class DrinkTypes(Resource):
    def get(self):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM Drink_Types")
        return jsonify(cursor.fetchall())


api.add_resource(DrinkTypes, "/drink/types")

if __name__ == "__main__":
    app.run(port=1997, debug=True)
