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


def is_authenticated(auth):
    if auth is None:
        return None
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
        return auth
    return None


class Authenticate(Resource):
    def get(self, auth=None):
        return jsonify(is_authenticated(auth))

    def post(self, auth=None):
        if request.form['USER'] == app.config['MYSQL_USER'] and request.form['PASS'] == app.config['MYSQL_PASSWORD']:
            cursor = mysql.connection.cursor()
            access_time = datetime.now()
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

    def put(self, id=None):
        auth = request.form['AUTH']
        if is_authenticated(auth) == auth:
            cursor = mysql.connection.cursor()
            name = request.form['NAME']
            desc = request.form['DESCRIPTION']
            flav = request.form['FLAVOURTEXT']
            typeID = int(request.form['TYPEID'])
            if id is not None:
                cursor.execute(
                    "UPDATE Drinks SET Name=%s,Description=%s,FlavourText=%s,DrinkTypeID=%s WHERE ID=%s",
                    [
                        name,
                        desc,
                        flav,
                        typeID,
                        id
                    ]
                )
                cursor.execute(
                    "SELECT * FROM Drinks WHERE ID=%s",
                    [
                        id
                    ]
                )
                return jsonify(cursor.fetchone())
            return jsonify(None), 404
        return jsonify(None), 403

    def post(self, id=None):
        auth = request.form['AUTH']
        if is_authenticated(auth) == auth:
            cursor = mysql.connection.cursor()
            name = request.form['NAME']
            desc = request.form['DESCRIPTION']
            flav = request.form['FLAVOURTEXT']
            typeID = int(request.form['TYPEID'])
            if id is not None:
                cursor.execute(
                    "UPDATE Drinks SET Name=%s,Description=%s,FlavourText=%s,DrinkTypeID=%s WHERE ID=%s",
                    [
                        name,
                        desc,
                        flav,
                        typeID,
                        id
                    ]
                )
                cursor.execute(
                    "SELECT * FROM Drinks WHERE ID=%s",
                    [
                        id
                    ]
                )
                return jsonify(cursor.fetchone())
            else:
                cursor.execute(
                    "INSERT INTO Drinks(Name,Description,FlavourText,DrinkTypeID) VALUES (%s,%s,%s,%s)",
                    [
                        name,
                        desc,
                        flav,
                        typeID
                    ]
                )
                cursor.execute(
                    "SELECT * FROM Drinks ORDER BY ID DESC LIMIT 1"
                )
                return jsonify(cursor.fetchone())
        else:
            return jsonify(None), 403


api.add_resource(Drink, *["/drink", "/drink/<int:id>"])


class DrinkTypes(Resource):
    def get(self):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM Drink_Types")
        return jsonify(cursor.fetchall())


api.add_resource(DrinkTypes, "/drink/type")


class Equipment(Resource):
    def get(self, drinkID=None):
        cursor = mysql.connection.cursor()
        if drinkID is None:
            cursor.execute("SELECT * FROM Equipment")
            return jsonify(cursor.fetchall())
        else:
            cursor.execute(
                "SELECT ID,Text FROM Equipment JOIN Drink_Equipment ON Drink_Equipment.EquipmentID=Equipment.ID WHERE "
                "Drink_Equipment.DrinkID=%s",
                [drinkID]
            )
            return jsonify(cursor.fetchall())


api.add_resource(Equipment, *["/equipment", "/drink/equipment/<int:drinkID>"])


class Flags(Resource):
    def get(self, drinkID=None, drinkType=None):
        cursor = mysql.connection.cursor()
        if drinkID is None and drinkType is None:
            cursor.execute(
                "SELECT * FROM Flags"
            )
            return jsonify(cursor.fetchall())
        elif drinkID is not None:
            cursor.execute(
                "SELECT DISTINCT ID, Text FROM Flags JOIN Drink_Flags ON FlagID=ID WHERE DrinkID=%s",
                [
                    drinkID
                ]
            )
            return jsonify(cursor.fetchall())
        else:
            cursor.execute(
                "SELECT DISTINCT Flags.ID, Flags.Text FROM Flags JOIN Drink_Flags ON FlagID=Flags.ID"
                " JOIN Drinks ON Drinks.ID=DrinkID WHERE DrinkTypeID=%s",
                [
                    drinkType
                ]
            )
            return jsonify(cursor.fetchall())
    def post(self, drinkID=None, drinkType=None):
        auth = request.form['AUTH']
        if is_authenticated(auth) == auth:
            cursor = mysql.connection.cursor()
            text = request.form['TEXT']
            cursor.execute(
                "INSERT INTO Flags(Text) VALUES (%s)",
                [
                    text
                ]
            )
            cursor.execute(
                "SELECT * FROM Flags ORDER BY ID DESC LIMIT 1"
            )
            return jsonify(cursor.fetchone())
        return jsonify(None), 403


api.add_resource(Flags, *["/flag", "/drink/<int:drinkID>/flag", "/drink/type/<int:drinkType>/flag"])
if __name__ == "__main__":
    app.run(port=1997, debug=True)
