from flask import Flask, jsonify, request
from flask_cors import CORS
from google.cloud import datastore

app = Flask(__name__)
CORS(app, resources={r'/*': {'origins': '*'}}, supports_credentials=True)


@app.route('/')
def hello():
    return "Hello, world!"


# Convert a hero into the format expected by the caller
def package_hero(hero: datastore.entity):
    new_hero = dict()
    try:
        new_hero['name'] = hero['name']
        new_hero['id'] = hero.key.id
    except KeyError:
        new_hero = None
    return new_hero


# Convert a list of heroes into the format expected by the caller
def package_hero_list(hero_list: list):
    new_hero_list = list()
    for hero in hero_list:
        new_hero_list.append(package_hero(hero))
    return new_hero_list


@app.route('/api/heroes/', methods=['GET'])
def get_heroes_api():
    # Get all heroes from the datastore database
    client = datastore.Client()
    query = client.query(kind='Hero')
    hero_list = list(query.fetch())

    # Get the parameters from the HTTP request
    query_parameters = request.args
    if 'name' in query_parameters:
        # Limit the list to just heroes with the string in their names
        hero_name = query_parameters['name'].lower()
        index = len(hero_list) - 1
        while index >= 0:
            if 'name' in hero_list[index]:
                if not(hero_name in hero_list[index]['name']):
                    del hero_list[index]
            index -= 1

    hero_list = package_hero_list(hero_list)

    return jsonify(hero_list)


@app.route('/api/heroes/<int:hero_id>', methods=['GET'])
def get_hero_api(hero_id: int):
    # Get the specific hero from the datastore database
    client = datastore.Client()
    try:
        hero = client.get(client.key('Hero', int(hero_id)))
    except ValueError:
        # If we managed to get a bad ID, just return None
        hero = None

    if hero is not None:
        hero = package_hero(hero)

    return jsonify(hero)


@app.route('/api/heroes/<int:hero_id>', methods=['DELETE'])
def delete_hero_api(hero_id: int):
    # Delete the hero from the datastore database
    client = datastore.Client()

    return_value = f'Hero {hero_id} deleted.'
    try:
        client.delete(client.key('Hero', int(hero_id)))
    except ValueError:
        # If we managed to get a bad ID, just return None
        return_value = f'Bad ID {hero_id}'

    return jsonify(return_value)


@app.route('/api/heroes/', methods=['PUT'])
def update_hero_api():
    client = datastore.Client()
    entity = datastore.entity.Entity()
    try:
        entity.key = client.key('Hero', int(request.json['id']))
        entity['name'] = request.json['name']
        client.put(entity)
        return_data = package_hero(entity)
    except ValueError:
        return_data = "Bad ID"

    return jsonify(return_data)


@app.route('/api/heroes/', methods=['POST'])
def add_hero_api():
    # Add the specific hero to the datastore database
    client = datastore.Client()
    entity = datastore.entity.Entity()
    entity.key = client.key('Hero')
    try:
        entity['name'] = request.json['name']
        client.put(entity)
        return_data = package_hero(entity)
    except KeyError:
        return_data = "Failed to provide a name"
    return jsonify(return_data)


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)
