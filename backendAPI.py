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
    def get(self, auth):
        return jsonify(is_authenticated(auth))

    def post(self):
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
        return jsonify(None), 403

    def delete(self, auth):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "DELETE FROM Auth WHERE CODE=%s",
            [
                auth
            ]
        )
        return None, 200


api.add_resource(Authenticate, *["/auth", "/auth/<string:auth>"])


class Drink(Resource):
    def get(self):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM Drinks")
        res = cursor.fetchall()
        return jsonify(res)

    def put(self, id):
        auth = request.form['AUTH']
        if is_authenticated(auth) == auth:
            cursor = mysql.connection.cursor()
            name = request.form['NAME']
            desc = request.form['DESCRIPTION']
            flav = request.form['FLAVOURTEXT']
            typeID = int(request.form['TYPEID'])
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
                "SELECT * FROM Drinks"
            )
            return jsonify(cursor.fetchall())
        return jsonify(None), 403

    def post(self):
        auth = request.form['AUTH']
        if is_authenticated(auth) == auth:
            cursor = mysql.connection.cursor()
            name = request.form['NAME']
            desc = request.form['DESCRIPTION']
            flav = request.form['FLAVOURTEXT']
            typeID = int(request.form['TYPEID'])
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
                "SELECT * FROM Drinks"
            )
            return jsonify(cursor.fetchall())
        return jsonify(None), 403

    def delete(self, id):
        auth = request.form['AUTH']
        if is_authenticated(auth):
            cursor = mysql.connection.cursor()
            cursor.execute(
                "DELETE FROM Drink_Equipment WHERE DrinkID=%s",
                [
                    id
                ]
            )
            cursor.execute(
                "DELETE FROM Drink_Flags WHERE DrinkID=%s",
                [
                    id
                ]
            )
            cursor.execute(
                "DELETE FROM Drink_Ingredients WHERE DrinkID=%s",
                [
                    id
                ]
            )
            cursor.execute(
                "DELETE FROM Drink_Skills WHERE DrinkID=%s",
                [
                    id
                ]
            )
            cursor.execute(
                "DELETE FROM Drink_Steps WHERE DrinkID=%s",
                [
                    id
                ]
            )
            cursor.execute(
                "DELETE FROM Drinks WHERE ID=%s",
                [
                    id
                ]
            )
            return None, 200
        return None, 403


api.add_resource(Drink, *["/drink", "/drink/<int:id>"])


class Type(Resource):
    def get(self):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM Drink_Types")
        return jsonify(cursor.fetchall())


api.add_resource(Type, "/type")


class Equipment(Resource):
    def get(self):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM Equipment")
        return jsonify(cursor.fetchall())

    def post(self):
        auth = request.form['AUTH']
        if is_authenticated(auth):
            cursor = mysql.connection.cursor()
            text = request.form['TEXT']
            cursor.execute(
                "INSERT INTO Equipment(Text) VALUES (%s)",
                [
                    text
                ]
            )
            cursor.execute(
                "SELECT * FROM Equipment"
            )
            return jsonify(cursor.fetchall())
        return jsonify(None), 403

    def put(self, equipmentID):
        auth = request.form['AUTH']
        if is_authenticated(auth):
            cursor = mysql.connection.cursor()
            text = request.form['TEXT']
            cursor.execute(
                "UPDATE Equipment SET Text=%s WHERE ID=%s",
                [
                    text,
                    equipmentID
                ]
            )
            cursor.execute(
                "SELECT * FROM Equipment"
            )
            return jsonify(cursor.fetchall())
        return jsonify(None), 403

    def delete(self, equipmentID):
        auth = request.form['AUTH']
        if is_authenticated(auth):
            cursor = mysql.connection.cursor()
            cursor.execute(
                "DELETE FROM Drink_Equipment WHERE EquipmentID=%s",
                [
                    equipmentID
                ]
            )
            cursor.execute(
                "DELETE FROM Equipment WHERE ID=%s",
                [
                    equipmentID
                ]
            )
            return None
        return None, 403


api.add_resource(Equipment, *["/equipment", "/equipment/<int:equipmentID>"])


class DrinkEquipment(Resource):
    def get(self, id):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT ID, Text FROM Equipment JOIN Drink_Equipment ON EquipmentID=ID WHERE DrinkID=%s",
            [
                id
            ]
        )
        return jsonify(cursor.fetchall())

    def post(self, id):
        auth = request.form['AUTH']
        if is_authenticated(auth):
            equipmentID = request.form['EQUIPMENTID']
            cursor = mysql.connection.cursor()
            cursor.execute(
                "INSERT INTO Drink_Equipment(DrinkID, EquipmentID) VALUES (%s, %s)",
                [
                    id,
                    equipmentID
                ]
            )
            cursor.execute(
                "SELECT ID, Text FROM Equipment JOIN Drink_Equipment ON EquipmentID=ID WHERE DrinkID=%s",
                [
                    id
                ]
            )
            return jsonify(cursor.fetchall())
        return None, 403

    def delete(self, id):
        auth = request.form['AUTH']
        if is_authenticated(auth):
            equipmentID = request.form['EQUIPMENTID']
            cursor = mysql.connection.cursor()
            cursor.execute(
                "DELETE FROM Drink_Equipment WHERE DrinkID=%s AND EquipmentID=%s",
                [
                    id,
                    equipmentID
                ]
            )
            cursor.execute(
                "SELECT ID, Text FROM Equipment JOIN Drink_Equipment ON EquipmentID=ID WHERE DrinkID=%s",
                [
                    id
                ]
            )
            return jsonify(cursor.fetchall())
        return None, 403


api.add_resource(DrinkEquipment, *["/drink/<int:id>/equipment"])


class Flag(Resource):
    def get(self, typeID=None):
        cursor = mysql.connection.cursor()
        if typeID is None:
            cursor.execute(
                "SELECT * FROM Flags"
            )
            return jsonify(cursor.fetchall())
        else:
            cursor.execute(
                "SELECT DISTINCT Flags.ID, Flags.Text FROM Flags JOIN Drink_Flags ON FlagID=Flags.ID"
                " JOIN Drinks ON Drinks.ID=DrinkID WHERE DrinkTypeID=%s",
                [
                    typeID
                ]
            )
            return jsonify(cursor.fetchall())

    def post(self):
        auth = request.form['AUTH']
        if is_authenticated(auth):
            cursor = mysql.connection.cursor()
            text = request.form['TEXT']
            cursor.execute(
                "INSERT INTO Flags(Text) VALUES (%s)",
                [
                    text
                ]
            )
            cursor.execute(
                "SELECT * FROM Flags"
            )
            return jsonify(cursor.fetchone())
        return jsonify(None), 403

    def put(self, flagID):
        auth = request.form['AUTH']
        if is_authenticated(auth) == auth:
            cursor = mysql.connection.cursor()
            text = request.form['TEXT']
            cursor.execute(
                "UPDATE Flags SET Text=%s WHERE ID=%s",
                [
                    text,
                    flagID
                ]
            )
            cursor.execute(
                "SELECT * FROM Flags"
            )
            return jsonify(cursor.fetchone())
        return jsonify(None), 403

    def delete(self, flagID):
        auth = request.form['AUTH']
        if is_authenticated(auth):
            cursor = mysql.connection.cursor()
            cursor.execute(
                "DELETE FROM Drink_Flags WHERE FlagID=%s",
                [
                    flagID
                ]
            )
            cursor.execute(
                "DELETE FROM Flags WHERE ID=%s",
                [
                    flagID
                ]
            )
            return None, 200
        return None, 403


api.add_resource(Flag,
                 *["/flag", "/type/flag/<int:typeID>", "/flag/<int:flagID>"])


class DrinkFlag(Resource):
    def get(self, id):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT ID, Text FROM Flags JOIN Drink_Flags WHERE DrinkID=%s",
            [
                id
            ]
        )
        return jsonify(cursor.fetchall())

    def post(self, id):
        auth = request.form['AUTH']
        if is_authenticated(auth):
            cursor = mysql.connection.cursor()
            flagID = request.form['FLAGID']
            cursor.execute(
                "INSERT INTO Drink_Flags(DrinkID, FlagID) VALUES (%s,%s)",
                [
                    id,
                    flagID
                ]
            )
            cursor.execute(
                "SELECT ID, Text FROM Flags JOIN Drink_Flags ON FlagID=ID WHERE DrinkID=%s",
                [
                    id
                ]
            )
            return jsonify(cursor.fetchall())
        return None, 403

    def delete(self, id):
        auth = request.form['AUTH']
        if is_authenticated(auth):
            cursor = mysql.connection.cursor()
            flagID = request.form['FLAGID']
            cursor.execute(
                "DELETE FROM Drink_Flags WHERE DrinkID=%s AND FlagID=%s",
                [
                    id,
                    flagID
                ]
            )
            cursor.execute(
                "SELECT ID, Text FROM Flags JOIN Drink_Flags ON FlagID=ID WHERE DrinkID=%s",
                [
                    id
                ]
            )
            return jsonify(cursor.fetchall())
        return None, 403


api.add_resource(DrinkFlag, *["/drink/<int:id>/flag"])


class Ingredient(Resource):
    def get(self):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM Ingredients"
        )
        return jsonify(cursor.fetchall())

    def post(self):
        auth = request.form['AUTH']
        if is_authenticated(auth):
            cursor = mysql.connection.cursor()
            name = request.form['NAME']
            cursor.execute(
                "INSERT INTO Ingredients(Name) VALUES (%s)",
                [
                    name
                ]
            )
            cursor.execute(
                "SELECT * FROM Ingredients"
            )
            return jsonify(cursor.fetchall())
        return None, 403

    def put(self, id):
        auth = request.form['AUTH']
        if is_authenticated(auth):
            cursor = mysql.connection.cursor()
            name = request.form['NAME']
            cursor.execute(
                "UPDATE Ingredients SET Name=%s WHERE ID=%s",
                [
                    name,
                    id
                ]
            )
            cursor.execute(
                "SELECT * FROM Ingredients"
            )
            return jsonify(cursor.fetchall())
        return None, 403

    def delete(self, id):
        auth = request.form['AUTH']
        if is_authenticated(auth):
            cursor = mysql.connection.cursor()
            cursor.execute(
                "DELETE FROM Drink_Ingredients WHERE IngredientID=%s",
                [
                    id
                ]
            )
            cursor.execute(
                "DELETE FROM Ingredients WHERE ID=%s",
                [
                    id
                ]
            )
            cursor.execute(
                "SELECT * FROM Ingredients"
            )
            return jsonify(cursor.fetchall())
        return None, 403


api.add_resource(Ingredient, *["/ingredient", "/ingredient/<int:id>"])


class DrinkIngredient(Resource):
    def get(self, id):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT Ingredient.ID, Ingredient.Name, Drink_Ingredients.Amount, Measurements.Name, Measurements.Unit, "
            "Measurements.Multiplier FROM Ingredients JOIN Drink_Ingredients ON IngredientID=Ingredients.ID JOIN "
            "Measurements ON Drink_Ingredients.MeasurementID=Measurements.ID WHERE DrinkID=%s",
            [
                id
            ]
        )
        return jsonify(cursor.fetchall())

    def post(self, id):
        auth = request.form['AUTH']
        if is_authenticated(auth):
            cursor = mysql.connection.cursor()
            ingredientID = request.form['INGREDIENTID']
            measurementID = request.form['MEASUREMENTID']
            amount = request.form['AMOUNT']
            cursor.execute(
                "INSERT INTO Drink_Ingredients(DrinkID, IngredientID, MeasurementID, Amount) VALUES (%s,%s,%s,%s)",
                [
                    id,
                    ingredientID,
                    measurementID,
                    amount
                ]
            )
            cursor.execute(
                "SELECT Ingredient.ID, Ingredient.Name, Drink_Ingredients.Amount, Measurements.Name, Measurements.Unit, "
                "Measurements.Multiplier FROM Ingredients JOIN Drink_Ingredients ON IngredientID=Ingredients.ID JOIN "
                "Measurements ON Drink_Ingredients.MeasurementID=Measurements.ID WHERE DrinkID=%s",
                [
                    id
                ]
            )
            return jsonify(cursor.fetchall())
        return None, 403

    def put(self, id, ingredientID):
        auth = request.form['AUTH']
        if is_authenticated(auth):
            cursor = mysql.connection.cursor()
            measurementID = request.form['MEASUREMENTID']
            amount = request.form['AMOUNT']
            cursor.execute(
                "UPDATE Drink_Ingredients SET IngredientID=%s, MeasurementID=%s, Amount=%s WHERE DrinkID=%s "
                "AND IngredientID=%s",
                [
                    ingredientID,
                    measurementID,
                    amount,
                    id,
                    ingredientID
                ]
            )
            cursor.execute(
                "SELECT Ingredient.ID, Ingredient.Name, Drink_Ingredients.Amount, Measurements.Name, Measurements.Unit, "
                "Measurements.Multiplier FROM Ingredients JOIN Drink_Ingredients ON IngredientID=Ingredients.ID JOIN "
                "Measurements ON Drink_Ingredients.MeasurementID=Measurements.ID WHERE DrinkID=%s",
                [
                    id
                ]
            )
            return jsonify(cursor.fetchall())
        return None, 403

    def delete(self, id, ingredientID):
        auth = request.form['AUTH']
        if is_authenticated(auth):
            cursor = mysql.connection.cursor()
            cursor.execute(
                "DELETE FROM Drink_Ingredients WHERE DrinkID=%s AND IngredientID=%s",
                [
                    id,
                    ingredientID
                ]
            )
            cursor.execute(
                "SELECT Ingredient.ID, Ingredient.Name, Drink_Ingredients.Amount, Measurements.Name, Measurements.Unit, "
                "Measurements.Multiplier FROM Ingredients JOIN Drink_Ingredients ON IngredientID=Ingredients.ID JOIN "
                "Measurements ON Drink_Ingredients.MeasurementID=Measurements.ID WHERE DrinkID=%s",
                [
                    id
                ]
            )
            return jsonify(cursor.fetchall())
        return None, 403


api.add_resource(DrinkIngredient, *["/drink/<int:id>/ingredient", "/drink/<int:id>/ingredient/<int:ingredientID>"])


class DrinkStep(Resource):
    def get(self, id):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM Drink_Steps WHERE DrinkID=%s",
            [
                id
            ]
        )
        return jsonify(cursor.fetchall())

    def post(self, id):
        auth = request.form['AUTH']
        if is_authenticated(auth):
            text = request.form['TEXT']
            cursor = mysql.connection.cursor()
            cursor.execute(
                "INSERT INTO Drink_Steps(DrinkID, Text) VALUES (%s,%s)",
                [
                    id,
                    text
                ]
            )
            cursor.execute(
                "SELECT * FROM Drink_Steps WHERE DrinkID=%s",
                [
                    id
                ]
            )
            return jsonify(cursor.fetchall())
        return None, 403

    def put(self, id, stepID):
        auth = request.form['AUTH']
        if is_authenticated(auth):
            text = request.form['TEXT']
            cursor = mysql.connection.cursor()
            cursor.execute(
                "UPDATE Drink_Steps SET Text=%s WHERE ID=%s",
                [
                    text,
                    stepID
                ]
            )
            cursor.execute(
                "SELECT * FROM Drink_Steps WHERE DrinkID=%s",
                [
                    id
                ]
            )
            return jsonify(cursor.fetchall())
        return None, 403

    def delete(self, id, stepID):
        auth = request.form['AUTH']
        if is_authenticated(auth):
            cursor = mysql.connection.cursor()
            cursor.execute(
                "DELETE FROM Drink_Steps WHERE ID=%s",
                stepID
            )
            cursor.execute(
                "SELECT * FROM Drink_Steps WHERE DrinkID=%s",
                [
                    id
                ]
            )
            return jsonify(cursor.fetchall())
        return None, 403


api.add_resource(DrinkStep, *["/drink/<int:id>/step", "/drink/<int:id>/step/<int:stepID>"])

if __name__ == "__main__":
    app.run(port=1997, debug=True)
