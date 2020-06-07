import re
import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


# helper(utility method) for pagination
def paginate_elements(elements):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE  # starting index
    end = start + QUESTIONS_PER_PAGE  # ending index

    formatted_elements = [element.format() for element in elements]
    current_elements = formatted_elements[start:end]

    return current_elements


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    # set up CORS to enable cross-domain requests, allowing all origins(*)
    cors = CORS(app, resources={"/api/*": {"origins": "*"}})

    # CORS headers
    @app.after_request
    def after_request(response):
        """
        Method sets access control
        """

        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,PATCH,DELETE,OPTIONS')

        return response

    @app.route('/api/categories')
    def get_categories():
        """
        Method handles GET requests for getting all categories
        :return:
        """

        # get all categories and add to a dictionary
        categories = Category.query.all()
        categories_dict = {}
        for category in categories:
            categories_dict[category.id] = category.type

        # abort if no category was found
        if len(categories_dict) == 0:
            abort(404)

        # return data to view
        return jsonify({
            'categories': categories_dict,
            'success': True
        })

    @app.route('/api/questions')
    def get_questions():
        """
         Method handles GET request for getting all questions
        :return:
        """

        # get all questions ordered by difficulty and paginate
        questions = Question.query.order_by(Question.difficulty).all()
        current_questions = paginate_elements(questions)

        # get all categories and add to a dictionary
        categories = Category.query.all()
        categories_dict = {}
        for category in categories:
            categories_dict[category.id] = category.type

        # abort if no question was found
        if len(current_questions) == 0:
            abort(404)

        # return data to view
        return jsonify({
            'categories': categories_dict,
            'questions': current_questions,
            'success': True,
            'questions_per_page': len(current_questions),
            'total_questions': len(Question.query.all())
        })

    @app.route('/api/questions/<int:question_id>', methods=['DELETE'])
    def delete_question(question_id):
        """
        Method handles DELETE request for deleting a specific question
        :param question_id:
        :return:
        """
        try:
            # get question by id
            question = Question.query.filter_by(id=question_id).one_or_none()

            # abort if no question was found(if None)
            if question is None:
                abort(404)

            # delete the question
            question.delete()

            # get the paginated list of questions
            questions = Question.query.order_by(Question.difficulty).all()
            current_questions = paginate_elements(questions)

            # return data to view show id deleted
            return jsonify({
                'questions': current_questions,
                'deleted': question_id,
                'success': True,
                'questions_per_page': len(current_questions),
                'total_questions': len(Question.query.all())
            })
        except:
            # abort if problem arises deleting a specific question
            abort(422)

    @app.route('/api/questions', methods=['POST'])
    def post_question():
        """
        Method handles POST requests for creating an entirely new question and searching questions
        :return:
        """

        # load and parse the request body
        body = request.get_json()

        # if the search term is present
        if body.get('searchTerm'):
            search_term = body.get('searchTerm')

            # load the search term from the request
            search_term = request.json.get('searchTerm')

            # query using search_term
            search_result = Question.query.filter(Question.question.ilike(f'%{search_term}%')).all()

            # abort if no result is found
            if len(search_result) == 0:
                abort(404)

            # paginate search result
            current_search_result = paginate_elements(search_result)

            # return data to view
            return jsonify({
                'success': True,
                'questions': current_search_result,
                'total_questions': len(current_search_result)
            })
        else:
            # load data from the *request* body
            question = body.get('question', '')
            answer = body.get('answer', '')
            category = body.get('category', '')
            difficulty = body.get('difficulty', '')

            # abort if all data fields are not populated
            if (question == '') or (answer == '') or (category == '') or (difficulty == ''):
                abort(422)

            try:
                question = Question(question=question, answer=answer, category=category, difficulty=difficulty)
                # create new question
                question.insert()

                # get the paginated list of questions
                questions = Question.query.order_by(Question.difficulty).all()
                current_questions = paginate_elements(questions)

                # return data to view show id created
                return jsonify({
                    'questions': current_questions,
                    'question_created': question.question,
                    'created': question.id,
                    'success': True,
                    'questions_per_page': len(current_questions),
                    'total_questions': len(Question.query.all())
                })
            except:
                # abort if problem arises creating a new question
                abort(422)

    @app.route('/api/categories/<int:category_id>/questions')
    def get_questions_by_category(category_id):
        """
        Method handles GET requests for getting questions based on a particular category.
        :param category_id:
        :return:
        """

        # get the category by id
        category = Category.query.filter_by(id=category_id).one_or_none()

        # abort if no category was found
        if category is None:
            abort(400)

        current_category = category.type

        questions_by_category = Question.query.filter_by(category=category.id).all()
        current_questions_by_category = paginate_elements(questions_by_category)

        # return data to view
        return jsonify({
            'current_category': current_category,
            'questions': current_questions_by_category,
            'success': True,
            'questions_per_page': len(current_questions_by_category),
            'total_questions': len(Question.query.all())
        })

    @app.route('/api/quizzes', methods=['POST'])
    def get_random_quiz_question():
        """
        Method handles POST request to play quiz
        :return:
        """

        try:

            # load the request body
            body = request.get_json()

            # abort if data parameters are not supplied
            if not ('quiz_category' in body and 'previous_questions' in body):
                abort(400)

            # load data from the request body
            category = body.get('quiz_category')
            previous_questions = body.get('previous_questions')

            # load available questions of a particular category
            if category['type'] == 'click':
                available_questions = Question.query.filter(
                    Question.id.notin_(previous_questions)).all()
            else:
                available_questions = Question.query.filter_by(
                    category=category['id']).filter(Question.id.notin_(previous_questions)).all()

            # generate a new random question
            new_question = available_questions[random.randrange(
                0, len(available_questions))].format() if len(available_questions) > 0 else None

            # return data to view
            return jsonify({
                'success': True,
                'question': new_question
            })
        except:
            abort(400)

    # error handlers

    @app.errorhandler(400)
    def bad_request(error):

        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    @app.errorhandler(404)
    def not_found(error):

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
            "message": "method not allowed"
        }), 405

    @app.errorhandler(422)
    def unprocessable(error):

        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(500)
    def server_error(error):

        return jsonify({
            'success': False,
            'error': 500,
            "message": "server error"
        })

    return app
