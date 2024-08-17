# Chatbot with Persistent Memory

This project is designed to implement a chatbot powered by a Large Language Model (LLM) that features persistent memory. The chatbot is capable of remembering information across sessions, which allows it to provide more contextually accurate and detailed responses over time.

## Project Description

The project consists of three key models that work together to create a chatbot with memory capabilities:

1. **Model 1**: This is the primary interaction model that processes user inputs and generates responses. It handles new information and generates detailed knowledge when required.
   
2. **Model 2**: This model is responsible for memory management. It updates or creates memory records based on new information provided by Model 1 and retrieves relevant memory data when needed.

3. **Model 3**: This model uses the memory data provided by Model 2 to generate responses that require contextual information, ensuring continuity and coherence in interactions.


### Project Structure

- **index.html**: This file contains the chat interface that allows users to interact with the chatbot. It makes API calls to the backend for processing.

- **app.py**: A Flask-based backend that provides the necessary APIs for the chatbot. 

- **model.py**: The `get_response` function within this file facilitates the interaction between the user and Model 1, with Model 2 and Model 3 being used as needed for memory-related tasks.


## Getting Started

To get started with the project, clone the repository and ensure you have all the necessary dependencies installed. You can then run the Flask app and set up the OpenAI API key and interact with the chatbot through the interface provided in `index.html`. Also, ensure the url for API endpoint is correct in index.html.