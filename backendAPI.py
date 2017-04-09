from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from flask_mysqldb import MySQL
from getpass import getpass
from datetime import datetime, timedelta

app = Flask(__name__)
api = Api(app)
app.config['MYSQL_DB'] = "drinKit"
app.config['MYSQL_HOST'] = "127.0.0.1"
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

mysql = None


class Authenticate(Resource):
    def get(self, auth):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM Auth WHERE CODE='{}'".format(auth))
        res = cursor.fetchone()
        if res is not None:
            access_time = datetime.now()
            query = "UPDATE Auth SET Expiry='{}' WHERE CODE='{}'".format(
                "{:%Y-%m-%d %H:%M:%s}".format(access_time + timedelta(hours=1)),
                auth
            )
            if res['Expiry'] < access_time:
                query = "DELETE FROM Auth WHERE CODE='{}'".format(auth)
                auth = None
            cursor.execute(query)
            mysql.connection.commit()
            return jsonify(auth)
        return jsonify(None)

    def post(self, auth):
        if request.form['USER'] == app.config['MYSQL_USER'] and request.form['PASS'] == app.config['MYSQL_PASSWORD']:
            cursor = mysql.connection.cursor()
            access_time = datetime.now()
            print('{:%Y%M%S%d%H%m}'.format(access_time))
            key = '{:.25}'.format(str(hash(int('{:%Y%M%S%d%H%m}'.format(access_time))) ** 2))
            cursor.execute("INSERT INTO Auth(CODE,Expiry) VALUES ('{}','{}')".format(
                key,
                "{:%Y-%m-%d %H:%M:%S}".format(access_time + timedelta(hours=1))
            ))
            mysql.connection.commit()
            return jsonify(key)
        return None, 403


class Drinks(Resource):
    def get(self):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM Drinks")
        res = cursor.fetchall()
        for i in range(len(res)):
            cursor.execute("SELECT * FROM Ingredients WHERE DrinkID={}".format(res[i]['ID']))
            res[i]['Ingredients'] = cursor.fetchall()
        return jsonify(res)


api.add_resource(Drinks, "/drinks")
api.add_resource(Authenticate, "/auth/<string:auth>")

if __name__ == "__main__":
    app.config['MYSQL_USER'] = input("MySQL Username: ")
    app.config['MYSQL_PASSWORD'] = getpass("MySQL Password: ")
    mysql = MySQL(app)
    app.run(port=1997, debug=True)
