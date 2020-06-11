import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

db_drop_and_create_all()


# ROUTES
@app.route('/drinks')
def get_drinks():
    """
     Method handles GET requests for getting all drinks
    :return:
    """

    # get all drinks
    drinks = Drink.query.all()

    # return data to view
    return jsonify({
        # list interpolation
        'drinks': [drink.short() for drink in drinks],
        'success': True
    }), 200


@app.route('/drinks-detail')
@requires_auth('get:drinks-detail')
def get_drinks_detail(jwt):
    """
     Method handles GET requests for getting drinks-detail
     :param jwt:
    :return:
    """

    # get all drinks
    drinks = Drink.query.all()

    # return data view
    return jsonify({
        # list interpolation
        'drinks': [drink.long() for drink in drinks],
        'success': True
    }), 200


@app.route('/drinks', methods=['POST'])
@requires_auth('post:drinks')
def create_drinks(payload):
    """
    Method handles POST requests to create drinks
    :param payload:
    :return:
    """

    # load and parse the request body
    body = request.get_json()

    # load data from the *request* body
    body_title = body.get('title')
    body_recipe = body.get('recipe')

    # ensure body_recipe is a dictionary
    if isinstance(body_recipe, dict):
        body_recipe = body_recipe

    try:
        # create a new drink
        drink = Drink(title=body_title, recipe=json.dumps(body_recipe))
        drink.insert()

        # return data to view
        return jsonify({
            'drinks': [drink.long()],
            'success': True
        }), 200
    except:
        # abort if problem arises creating a new drink
        abort(422)


@app.route('/drinks/<int:drink_id>', methods=['PATCH'])
@requires_auth('patch:drinks')
def update_drink(payload, drink_id):
    """
    Method handles PATCH request to update drinks
    :param payload:
    :param drink_id:
    :return:
    """

    # load and parse the request body
    body = request.get_json()

    # load data from the *request* body
    body_title = body.get('title')
    body_recipe = body.get('recipe')

    # ensure body_recipe is a dictionary
    if isinstance(body_recipe, dict):
        body_recipe = body_recipe

    try:
        # get drink by id
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

        # abort if no drink was found
        if not drink:
            abort(404)

        # update drink
        drink.title = body_title
        drink.recipe = json.dumps(body_recipe)
        drink.update()

        # return data to view
        return jsonify({
            'drinks': [drink.long()],
            'success': True
        }), 200
    except:
        abort(422)


@app.route('/drinks/<int:drink_id>', methods=['DELETE'])
@requires_auth('delete:drinks')
def delete_drink(payload, drink_id):
    """
    Method handles DELETE request to delete drinks
    :param payload:
    :param drink_id:
    :return:
    """

    try:
        # get drink by id
        drink = Drink.query.filter(Drink.id == drink_id).one_or_none()

        # abort if no drink was found
        if drink is None:
            abort(404)

        # delete drink
        drink.delete()

        # return data to view
        return jsonify({
            'deleted': drink_id,
            'success': True
        }), 200
    except:
        abort(422)


@app.errorhandler(400)
def bad_request(error):
    return jsonify({
        "success": False,
        "error": 400,
        "message": 'bad request'
    }), 400


@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 401,
        "message": 'unauthorized'
    }), 401


@app.errorhandler(403)
def unauthorized(error):
    return jsonify({
        "success": False,
        "error": 403,
        "message": 'forbidden'
    }), 403


@app.errorhandler(404)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 404,
        "message": "resource not found"
    }), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "success": False,
        "error": 405,
        "message": 'method not allowed'
    }), 405


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({
        "success": False,
        "error": 422,
        "message": "unprocessable"
    }), 422


@app.errorhandler(500)
def internal_server_error(error):
    return jsonify({
        "success": False,
        "error": 500,
        "message": 'server error'
    }), 500


# custom error
@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({
        "success": False,
        "error": error.status_code,
        "message": error.error['description']
    }), error.status_code
