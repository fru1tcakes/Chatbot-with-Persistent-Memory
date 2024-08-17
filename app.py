from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from model import *

app = Flask(__name__)

# Initialize CORS for the Flask app
CORS(app)

# Configure the app to use SQLite with SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///example.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the SQLAlchemy object
db = SQLAlchemy(app)

class Memory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.Text(), nullable=False)
    detail = db.Column(db.Text(), nullable=False)

# Create the database and tables
with app.app_context():
    db.create_all()

# Define a basic route to test the setup
@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/start_conversation', methods=['POST'])
def start_conversation():
    # Logic to start a conversation with Model 1
    return jsonify({"message": "Conversation started"})

@app.route('/chat', methods=['POST'])
def chat():
    user_msg = request.json.get('message')
    # Generate a response (here we simply echo the message for simplicity)
    response_msg = get_response(user_msg)
    return jsonify({'response': response_msg})

@app.route('/store_memory', methods=['POST'])
def store_memory():
    try:
        # Extract the description and detail from the request
        data = request.json
        description = data.get('description')
        detail = data.get('detail')

        # Create a new Memory object
        new_memory = Memory(description=description, detail=detail)

        # Add the new Memory object to the database and commit the transaction
        db.session.add(new_memory)
        db.session.commit()

        # Return a success message
        return jsonify({'message': f'New Memory: {new_memory.description}', 'id': new_memory.id})
    except Exception as e:
        # Handle any errors that occur
        return jsonify({'error': str(e)})

@app.route('/memories', methods=['GET'])
def get_all_memories():
    try:
        # Retrieve all memories from the database
        memories = Memory.query.all()
        # Convert the memories to a list of dictionaries
        memories_list = [{'id': memory.id, 'description': memory.description, 'detail': memory.detail} for memory in memories]
        return jsonify(memories_list)
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/memory/<int:id>', methods=['GET'])
def get_memory_by_id(id):
    try:
        # Retrieve the memory by ID
        memory = Memory.query.get(id)
        if memory is None:
            return jsonify({'error': 'Memory not found'}), 404
        return jsonify({'id': memory.id, 'description': memory.description, 'detail': memory.detail})
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/memory/<int:id>', methods=['PUT'])
def update_memory_by_id(id):
    try:
        # Retrieve the memory by ID
        memory = Memory.query.get(id)
        if memory is None:
            return jsonify({'error': 'Memory not found'}), 404

        # Extract the description and detail from the request
        data = request.json
        print(data)
        memory.description = data.get('description', memory.description)
        memory.detail = data.get('detail', memory.detail)

        # Commit the changes to the database
        db.session.commit()

        return jsonify({'message': f'Memory updated successfully: {memory.description}'})
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)