import random
import string
import os.path
from datetime import datetime, timedelta

from flask import Flask, jsonify, request
from flask_mysqldb import MySQL
from flask_restful import Resource, Api

app = Flask(__name__)
api = Api(app)
app.config["MYSQL_DB"] = "drinKit"
app.config["MYSQL_HOST"] = "127.0.0.1"
app.config["MYSQL_CURSORCLASS"] = "DictCursor"
app.config["MYSQL_USER"] = ""
app.config["MYSQL_PASSWORD"] = ""
mysql = MySQL(app)


@app.after_request
def add_xss(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


def is_authenticated(auth):
    if auth is None:
        return None
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT * FROM Auth WHERE CODE=%s", [auth])
    res = cursor.fetchone()
    if res is not None:
        access_time = datetime.now()
        if res["Expiry"] < access_time:
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


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic
class Authenticate(Resource):
    def get(self, auth):
        return jsonify(is_authenticated(auth))

    def post(self):
        if request.form["USER"] == app.config["MYSQL_USER"] and request.form["PASS"] == app.config["MYSQL_PASSWORD"]:
            cursor = mysql.connection.cursor()
            access_time = datetime.now()
            key = "".join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(50))
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
        mysql.connection.commit()
        return None, 200


# noinspection PyTypeChecker
api.add_resource(Authenticate, *["/auth", "/auth/<string:auth>"])


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic
class Drink(Resource):
    def get(self):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM Drinks")
        res = cursor.fetchall()
        return jsonify(res)

    def put(self, classid):
        auth = request.form['AUTH']
        if is_authenticated(auth) == auth:
            cursor = mysql.connection.cursor()
            name = request.form['NAME']
            desc = request.form['DESCRIPTION']
            flav = request.form['FLAVOURTEXT']
            typeid = int(request.form['TYPEID'])
            cursor.execute(
                "UPDATE Drinks SET Name=%s,Description=%s,FlavourText=%s,DrinkTypeID=%s WHERE ID=%s",
                [
                    name,
                    desc,
                    flav,
                    typeid,
                    classid
                ]
            )
            cursor.execute(
                "SELECT * FROM Drinks"
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return jsonify(None), 403

    def post(self):
        auth = request.form['AUTH']
        if is_authenticated(auth) == auth:
            cursor = mysql.connection.cursor()
            name = request.form['NAME']
            desc = request.form['DESCRIPTION']
            flav = request.form['FLAVOURTEXT']
            typeid = int(request.form['TYPEID'])
            cursor.execute(
                "INSERT INTO Drinks(Name,Description,FlavourText,DrinkTypeID) VALUES (%s,%s,%s,%s)",
                [
                    name,
                    desc,
                    flav,
                    typeid
                ]
            )
            cursor.execute(
                "SELECT * FROM Drinks"
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return jsonify(None), 403

    def delete(self, classid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            cursor.execute(
                "DELETE FROM Drink_Equipment WHERE DrinkID=%s",
                [
                    classid
                ]
            )
            cursor.execute(
                "DELETE FROM Drink_Flags WHERE DrinkID=%s",
                [
                    classid
                ]
            )
            cursor.execute(
                "DELETE FROM Drink_Ingredients WHERE DrinkID=%s",
                [
                    classid
                ]
            )
            cursor.execute(
                "DELETE FROM Drink_Skills WHERE DrinkID=%s",
                [
                    classid
                ]
            )
            cursor.execute(
                "DELETE FROM Drink_Steps WHERE DrinkID=%s",
                [
                    classid
                ]
            )
            cursor.execute(
                "DELETE FROM Drinks WHERE ID=%s",
                [
                    classid
                ]
            )
            mysql.connection.commit()
            return None, 200
        return None, 403


# noinspection PyTypeChecker
api.add_resource(Drink, *["/drink", "/drink/<int:classid>"])


class DrinkImage(Resource):
    def get(self, classid):
        if os.path.isfile("/var/www/redir/drinKit/images/" + str(classid) + ".png"):
            return "http://46.101.52.91/drinKit/images/" + str(classid) + ".png"
        return "http://46.101.52.91/drinKit/images/PlaceHolder.png"

    def put(self, classid):
        if is_authenticated(request.form['AUTH']):
            image = open("/var/www/redir/drinKit/images/" + str(classid) + ".png", "bw")
            image.write(request.files['IMAGE'])
            return None
        return None, 403


api.add_resource(DrinkImage, *["/drink/image/<int:classid>"])


# noinspection PyMethodMayBeStatic
class Type(Resource):
    def get(self):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM Drink_Types")
        return jsonify(cursor.fetchall())


# noinspection PyTypeChecker
api.add_resource(Type, "/type")


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic
class Equipment(Resource):
    def get(self):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM Equipment ORDER BY Text")
        return jsonify(cursor.fetchall())

    def post(self):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            text = request.form['TEXT']
            cursor.execute(
                "INSERT INTO Equipment(Text) VALUES (%s)",
                [
                    text
                ]
            )
            cursor.execute("SELECT * FROM Equipment ORDER BY Text")
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return jsonify(None), 403

    def put(self, equipmentid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            text = request.form['TEXT']
            cursor.execute(
                "UPDATE Equipment SET Text=%s WHERE ID=%s",
                [
                    text,
                    equipmentid
                ]
            )
            cursor.execute("SELECT * FROM Equipment ORDER BY Text")
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return jsonify(None), 403

    def delete(self, equipmentid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            cursor.execute(
                "DELETE FROM Drink_Equipment WHERE EquipmentID=%s",
                [
                    equipmentid
                ]
            )
            cursor.execute(
                "DELETE FROM Equipment WHERE ID=%s",
                [
                    equipmentid
                ]
            )
            cursor.execute("SELECT * FROM Equipment ORDER BY Text")
            mysql.connection.commit()
            return None
        return None, 403


# noinspection PyTypeChecker
api.add_resource(Equipment, *["/equipment", "/equipment/<int:equipmentid>"])


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic
class DrinkEquipment(Resource):
    def get(self, classid):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT ID, Text FROM Equipment JOIN Drink_Equipment ON EquipmentID=ID WHERE DrinkID=%s",
            [
                classid
            ]
        )
        return jsonify(cursor.fetchall())

    def post(self, classid):
        if is_authenticated(request.form['AUTH']):
            equipmentid = request.form['EQUIPMENTID']
            cursor = mysql.connection.cursor()
            cursor.execute(
                "INSERT INTO Drink_Equipment(DrinkID, EquipmentID) VALUES (%s, %s)",
                [
                    classid,
                    equipmentid
                ]
            )
            cursor.execute(
                "SELECT ID, Text FROM Equipment JOIN Drink_Equipment ON EquipmentID=ID WHERE DrinkID=%s",
                [
                    classid
                ]
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403

    def delete(self, classid, equipmentid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            cursor.execute(
                "DELETE FROM Drink_Equipment WHERE DrinkID=%s AND EquipmentID=%s",
                [
                    classid,
                    equipmentid
                ]
            )
            cursor.execute(
                "SELECT ID, Text FROM Equipment JOIN Drink_Equipment ON EquipmentID=ID WHERE DrinkID=%s",
                [
                    classid
                ]
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403


# noinspection PyTypeChecker
api.add_resource(DrinkEquipment, *["/drink/<int:classid>/equipment",
                                   "/drink/<int:classid>/equipment/<int:equipmentid>"])


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic
class Flag(Resource):
    def get(self, typeid=None):
        cursor = mysql.connection.cursor()
        if typeid is None:
            cursor.execute(
                "SELECT * FROM Flags"
            )
            return jsonify(cursor.fetchall())
        else:
            cursor.execute(
                "SELECT DISTINCT Flags.ID, Flags.Text FROM Flags JOIN Drink_Flags ON FlagID=Flags.ID"
                " JOIN Drinks ON Drinks.ID=DrinkID WHERE DrinkTypeID=%s",
                [
                    typeid
                ]
            )
            return jsonify(cursor.fetchall())

    def post(self):
        if is_authenticated(request.form['AUTH']):
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
            mysql.connection.commit()
            return jsonify(cursor.fetchone())
        return jsonify(None), 403

    def put(self, flagid):
        auth = request.form['AUTH']
        if is_authenticated(auth) == auth:
            cursor = mysql.connection.cursor()
            text = request.form['TEXT']
            cursor.execute(
                "UPDATE Flags SET Text=%s WHERE ID=%s",
                [
                    text,
                    flagid
                ]
            )
            cursor.execute(
                "SELECT * FROM Flags"
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchone())
        return jsonify(None), 403

    def delete(self, flagid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            cursor.execute(
                "DELETE FROM Drink_Flags WHERE FlagID=%s",
                [
                    flagid
                ]
            )
            cursor.execute(
                "DELETE FROM Flags WHERE ID=%s",
                [
                    flagid
                ]
            )
            mysql.connection.commit()
            return None, 200
        return None, 403


# noinspection PyTypeChecker
api.add_resource(Flag,
                 *["/flag", "/type/flag/<int:typeid>", "/flag/<int:flagid>"])


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic
class DrinkFlag(Resource):
    def get(self, classid):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT ID, Text FROM Flags JOIN Drink_Flags ON FlagID=ID WHERE DrinkID=%s",
            [
                classid
            ]
        )
        return jsonify(cursor.fetchall())

    def post(self, classid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            flagid = request.form['FLAGID']
            cursor.execute(
                "INSERT INTO Drink_Flags(DrinkID, FlagID) VALUES (%s,%s)",
                [
                    classid,
                    flagid
                ]
            )
            cursor.execute(
                "SELECT ID, Text FROM Flags JOIN Drink_Flags ON FlagID=ID WHERE DrinkID=%s",
                [
                    classid
                ]
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403

    def delete(self, classid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            flagid = request.form['FLAGID']
            cursor.execute(
                "DELETE FROM Drink_Flags WHERE DrinkID=%s AND FlagID=%s",
                [
                    classid,
                    flagid
                ]
            )
            cursor.execute(
                "SELECT ID, Text FROM Flags JOIN Drink_Flags ON FlagID=ID WHERE DrinkID=%s",
                [
                    classid
                ]
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403


# noinspection PyTypeChecker
api.add_resource(DrinkFlag, *["/drink/<int:classid>/flag"])


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic
class Ingredient(Resource):
    def get(self):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM Ingredients ORDER BY Name"
        )
        return jsonify(cursor.fetchall())

    def post(self):
        if is_authenticated(request.form['AUTH']):
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
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403

    def put(self, classid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            name = request.form['NAME']
            cursor.execute(
                "UPDATE Ingredients SET Name=%s WHERE ID=%s",
                [
                    name,
                    classid
                ]
            )
            cursor.execute(
                "SELECT * FROM Ingredients"
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403

    def delete(self, classid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            cursor.execute(
                "DELETE FROM Drink_Ingredients WHERE IngredientID=%s",
                [
                    classid
                ]
            )
            cursor.execute(
                "DELETE FROM Ingredients WHERE ID=%s",
                [
                    classid
                ]
            )
            cursor.execute(
                "SELECT * FROM Ingredients"
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403


# noinspection PyTypeChecker
api.add_resource(Ingredient, *["/ingredient", "/ingredient/<int:classid>"])


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic
class DrinkIngredient(Resource):
    def get(self, classid):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT Ingredients.ID, Ingredients.Name, Drink_Ingredients.Amount, Measurements.Name AS mName, "
            "Measurements.Unit, Measurements.Multiplier, Measurements.TypeID FROM Ingredients JOIN Drink_Ingredients "
            "ON IngredientID=Ingredients.ID JOIN Measurements ON Drink_Ingredients.MeasurementID=Measurements.ID WHERE "
            "DrinkID=%s",
            [
                classid
            ]
        )
        return jsonify(cursor.fetchall())

    def post(self, classid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            ingredientid = request.form['INGREDIENTID']
            measurementid = request.form['MEASUREMENTID']
            amount = request.form['AMOUNT']
            cursor.execute(
                "INSERT INTO Drink_Ingredients(DrinkID, IngredientID, MeasurementID, Amount) VALUES (%s,%s,%s,%s)",
                [
                    classid,
                    ingredientid,
                    measurementid,
                    amount
                ]
            )
            cursor.execute(
                "SELECT Ingredients.ID, Ingredients.Name, Drink_Ingredients.Amount, Measurements.Name AS mName, "
                "Measurements.Unit, Measurements.Multiplier, Measurements.TypeID FROM Ingredients JOIN Drink_Ingredients "
                "ON IngredientID=Ingredients.ID JOIN Measurements ON Drink_Ingredients.MeasurementID=Measurements.ID WHERE "
                "DrinkID=%s",
                [
                    classid
                ]
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403

    def put(self, classid, ingredientid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            measurementid = request.form['MEASUREMENTID']
            amount = request.form['AMOUNT']
            cursor.execute(
                "UPDATE Drink_Ingredients SET IngredientID=%s, MeasurementID=%s, Amount=%s WHERE DrinkID=%s "
                "AND IngredientID=%s",
                [
                    ingredientid,
                    measurementid,
                    amount,
                    classid,
                    ingredientid
                ]
            )
            cursor.execute(
                "SELECT Ingredients.ID, Ingredients.Name, Drink_Ingredients.Amount, Measurements.Name AS mName, "
                "Measurements.Unit, Measurements.Multiplier, Measurements.TypeID FROM Ingredients JOIN Drink_Ingredients "
                "ON IngredientID=Ingredients.ID JOIN Measurements ON Drink_Ingredients.MeasurementID=Measurements.ID WHERE "
                "DrinkID=%s",
                [
                    classid
                ]
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403

    def delete(self, classid, ingredientid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            cursor.execute(
                "DELETE FROM Drink_Ingredients WHERE DrinkID=%s AND IngredientID=%s",
                [
                    classid,
                    ingredientid
                ]
            )
            cursor.execute(
                "SELECT Ingredients.ID, Ingredients.Name, Drink_Ingredients.Amount, Measurements.Name AS mName, "
                "Measurements.Unit, Measurements.Multiplier, Measurements.TypeID FROM Ingredients JOIN Drink_Ingredients "
                "ON IngredientID=Ingredients.ID JOIN Measurements ON Drink_Ingredients.MeasurementID=Measurements.ID WHERE "
                "DrinkID=%s",
                [
                    classid
                ]
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403


# noinspection PyTypeChecker
api.add_resource(DrinkIngredient, *["/drink/<int:classid>/ingredient",
                                    "/drink/<int:classid>/ingredient/<int:ingredientid>"])


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic
class DrinkStep(Resource):
    def get(self, classid):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM Drink_Steps WHERE DrinkID=%s",
            [
                classid
            ]
        )
        return jsonify(cursor.fetchall())

    def post(self, classid):
        if is_authenticated(request.form['AUTH']):
            text = request.form['TEXT']
            cursor = mysql.connection.cursor()
            cursor.execute(
                "INSERT INTO Drink_Steps(DrinkID, Text) VALUES (%s,%s)",
                [
                    classid,
                    text
                ]
            )
            cursor.execute(
                "SELECT * FROM Drink_Steps WHERE DrinkID=%s",
                [
                    classid
                ]
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403

    def put(self, classid, stepid):
        if is_authenticated(request.form['AUTH']):
            text = request.form['TEXT']
            cursor = mysql.connection.cursor()
            cursor.execute(
                "UPDATE Drink_Steps SET Text=%s WHERE ID=%s",
                [
                    text,
                    stepid
                ]
            )
            cursor.execute(
                "SELECT * FROM Drink_Steps WHERE DrinkID=%s",
                [
                    classid
                ]
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403

    def delete(self, classid, stepid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            cursor.execute(
                "DELETE FROM Drink_Steps WHERE ID=%s",
                [
                    stepid
                ]
            )
            cursor.execute(
                "SELECT * FROM Drink_Steps WHERE DrinkID=%s",
                [
                    classid
                ]
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403


# noinspection PyTypeChecker
api.add_resource(DrinkStep, *["/drink/<int:classid>/step", "/drink/<int:classid>/step/<int:stepid>"])


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic
class MeasurementType(Resource):
    def get(self):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM Measurement_Types"
        )
        return jsonify(cursor.fetchall())

    def post(self):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            text = request.form['TEXT']
            cursor.execute(
                "INSERT INTO Measurement_Types(Text) VALUES (%s)",
                [
                    text
                ]
            )
            cursor.execute(
                "SELECT * FROM Measurement_Types"
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403

    def put(self, classid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            text = request.form['TEXT']
            cursor.execute(
                "UPDATE Measurement_Types SET Text=%s WHERE ID=%s",
                [
                    text,
                    classid
                ]
            )
            cursor.execute(
                "SELECT * FROM Measurement_Types"
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403

    def delete(self, classid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            cursor.execute(
                "DELETE Drink_Ingredients FROM Drink_Ingredients JOIN Measurements ON MeasurementID=ID WHERE TypeID=%s",
                [
                    classid
                ]
            )
            cursor.execute(
                "DELETE FROM Measurements WHERE TypeID=%s",
                [
                    classid
                ]
            )
            cursor.execute(
                "DELETE FROM Measurement_Types WHERE ID=%s",
                [
                    classid
                ]
            )
            cursor.execute(
                "SELECT * FROM Measurement_Types"
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403


# noinspection PyTypeChecker
api.add_resource(MeasurementType, *["/measurement/type", "/measurement/type/<int:classid>"])


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic
class Measurement(Resource):
    def get(self):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM Measurements ORDER BY Multiplier DESC"
        )
        return jsonify(cursor.fetchall())

    def post(self):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            typeid = request.form['TYPEID']
            name = request.form['NAME']
            unit = request.form['UNIT']
            multiplier = request.form['MULTIPLIER']
            cursor.execute(
                "INSERT INTO Measurements(TypeID, Name, Unit, Multiplier) VALUES (%s,%s,%s,%s)",
                [
                    typeid,
                    name,
                    unit,
                    multiplier
                ]
            )
            cursor.execute(
                "SELECT * FROM Measurements"
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403

    def put(self, classid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            typeid = request.form['TYPEID']
            name = request.form['NAME']
            unit = request.form['UNIT']
            multiplier = request.form['MULTIPLIER']
            cursor.execute(
                "UPDATE Measurements SET Name=%s,TypeID=%s,Unit=%s,Multiplier=%s WHERE ID=%s",
                [
                    name,
                    typeid,
                    unit,
                    multiplier,
                    classid
                ]
            )
            cursor.execute(
                "SELECT * FROM Measurements"
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403

    def delete(self, classid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            cursor.execute(
                "DELETE FROM Measurements WHERE ID=%s",
                [
                    classid
                ]
            )
            cursor.execute(
                "SELECT * FROM Measurements"
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403


# noinspection PyTypeChecker
api.add_resource(Measurement, *["/measurement", "/measurement/<int:classid>"])


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic
class Skill(Resource):
    def get(self):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM Skills"
        )
        return jsonify(cursor.fetchall())

    def post(self):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            difficultyid = request.form['DIFFICULTYID']
            name = request.form['NAME']
            cursor.execute(
                "INSERT INTO Skills(DifficultyID, Name) VALUES (%s, %s)",
                [
                    difficultyid,
                    name
                ]
            )
            cursor.execute(
                "SELECT * FROM Skills"
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403

    def put(self, classid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            difficultyid = request.form['DIFFICULTYID']
            name = request.form['NAME']
            cursor.execute(
                "UPDATE Skills SET Name=%s, DifficultyID=%s WHERE ID=%s",
                [
                    name,
                    difficultyid,
                    classid
                ]
            )
            cursor.execute(
                "SELECT * FROM Skills"
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403

    def delete(self, classid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            cursor.execute(
                "DELETE FROM Skill_Steps WHERE SkillID=%s",
                [
                    classid
                ]
            )
            cursor.execute(
                "DELETE FROM Drink_Skills WHERE SkillID=%s",
                [
                    classid
                ]
            )
            cursor.execute(
                "DELETE FROM Skills WHERE ID=%s",
                [
                    classid
                ]
            )
            cursor.execute(
                "SELECT * FROM Skills"
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403


# noinspection PyTypeChecker
api.add_resource(Skill, *["/skill", "/skill/<int:classid>"])


# noinspection PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic,PyMethodMayBeStatic
class SkillStep(Resource):
    def get(self, classid):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM Skill_Steps WHERE SkillID=%s",
            [
                classid
            ]
        )
        return jsonify(cursor.fetchall())

    def post(self, classid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            text = request.form['TEXT']
            cursor.execute(
                "INSERT INTO Skill_Steps(SkillID, Text) VALUES (%s,%s)",
                [
                    classid,
                    text
                ]
            )
            cursor.execute(
                "SELECT * FROM Skill_Steps WHERE SkillID=%s",
                [
                    classid
                ]
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403

    def put(self, classid, stepid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            text = request.form['TEXT']
            cursor.execute(
                "UPDATE Skill_Steps SET Text=%s WHERE ID=%s",
                [
                    text,
                    stepid
                ]
            )
            cursor.execute(
                "SELECT * FROM Skill_Steps WHERE SkillID=%s",
                [
                    classid
                ]
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403

    def delete(self, classid, stepid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            cursor.execute(
                "DELETE FROM Skill_Steps WHERE ID=%s",
                [
                    stepid
                ]
            )
            cursor.execute(
                "SELECT * FROM Skill_Steps WHERE SkillID=%s",
                [
                    classid
                ]
            )
            mysql.connection.commit()
            return jsonify(cursor.fetchall())
        return None, 403


# noinspection PyTypeChecker
api.add_resource(SkillStep, *["/skill/<int:classid>/step", "/skill/<int:classid>/step/<int:stepid>"])


class SkillDifficulty(Resource):
    def get(self):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT * FROM Skill_Difficulty"
        )
        return jsonify(cursor.fetchall())

    def post(self):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            text = request.form['TEXT']
            cursor.execute(
                "INSERT INTO Skill_Difficulty(Text) VALUES (%s)",
                [
                    text
                ]
            )
            mysql.connection.commit()
            cursor.execute(
                "SELECT * FROM Skill_Difficulty"
            )
            return jsonify(cursor.fetchall())
        return None, 403

    def put(self, classid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            text = request.form['TEXT']
            cursor.execute(
                "UPDATE Skill_Difficulty SET Text=%s WHERE ID=%s",
                [
                    text,
                    classid
                ]
            )
            mysql.connection.commit()
            cursor.execute(
                "SELECT * FROM Skill_Difficulty"
            )
            return jsonify(cursor.fetchall())
        return None, 403

    def delete(self, classid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            cursor.execute(
                "DELETE Drink_Skills FROM Drink_Skills JOIN Skills ON SkillID=ID WHERE DifficultyID=%s",
                [
                    classid
                ]
            )
            cursor.execute(
                "DELETE Skill_Steps FROM Skill_Steps JOIN Skills ON SkillID=ID WHERE DifficultyID=%s",
                [
                    classid
                ]
            )
            cursor.execute(
                "DELETE FROM Skills WHERE DifficultyID=%s",
                [
                    classid
                ]
            )
            cursor.execute(
                "DELETE FROM Skill_Difficulty WHERE ID=%s",
                [
                    classid
                ]
            )
            mysql.connection.commit()
            cursor.execute(
                "SELECT * FROM Skill_Difficulty"
            )
            return jsonify(cursor.fetchall())
        return None, 403


api.add_resource(SkillDifficulty, *["/skill/difficulty", "/skill/difficulty/<int:classid>"])


class DrinkSkill(Resource):
    def get(self, drinkid):
        cursor = mysql.connection.cursor()
        cursor.execute(
            "SELECT Skills.* FROM Drink_Skills JOIN Skills ON SkillID=ID WHERE DrinkID=%s",
            [
                drinkid
            ]
        )
        return jsonify(cursor.fetchall())

    def post(self, drinkid, classid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            cursor.execute(
                "INSERT INTO Drink_Skills(DrinkID, SkillID) VALUES (%s,%s)",
                [
                    drinkid,
                    classid
                ]
            )
            mysql.connection.commit()
            cursor.execute(
                "SELECT Skills.* FROM Drink_Skills JOIN Skills ON SkillID=ID WHERE DrinkID=%s",
                [
                    drinkid
                ]
            )
            return jsonify(cursor.fetchall())
        return None, 403

    def delete(self, drinkid, classid):
        if is_authenticated(request.form['AUTH']):
            cursor = mysql.connection.cursor()
            cursor.execute(
                "DELETE FROM Drink_Skills WHERE DrinkID=%s AND SkillID=%s",
                [
                    drinkid,
                    classid
                ]
            )
            mysql.connection.commit()
            cursor.execute(
                "SELECT Skills.* FROM Drink_Skills JOIN Skills ON SkillID=ID WHERE DrinkID=%s",
                [
                    drinkid
                ]
            )
            return jsonify(cursor.fetchall())
        return None, 403


api.add_resource(DrinkSkill, *["/drink/<int:drinkid>/skill", "/drink/<int:drinkid>/skill/<int:classid>"])

if __name__ == "__main__":
    app.run(port=1997)
