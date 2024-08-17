import json
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')

# print(api_key)

client = OpenAI(api_key=api_key)

assistant = client.beta.assistants.create(
  name="Chat Bot with Memory",
      instructions= """
    1. You are a chat bot that has access to memory that is developed through past conversations.
    2. You talk with the user. You can take help of the memory function only if you need to find answer to a user query that requires memory which user might have provided in previous convos.
    3. You use the function by providing it with the Question you want the answer for.
    4. At the end of convo or if the user asks you to store a new memory or update. You call the New Memory function with 'Text' that contains all information you learned in this conversation. 
 """ ,
  tools= [
    {
      "type": "function",
      "function": {
        "name": "new_memory",
        "description": "Create/Updates a memory in the database.",
        "parameters": {
          "type": "object",
          "properties": {
            "text": {
              "type": "string",
              "description": "The original memory block text that needs to be indexed and stored."
            }
          },
          "required": [
            "text"
          ]
        }
      }
    },
    {
      "type": "function",
      "function": {
        "name": "use_memory",
        "description": "Uses the memory tool to retrieve a response based on the provided text.",
        "parameters": {
          "type": "object",
          "properties": {
            "text": {
              "type": "string",
              "description": "The text input used to query the memory."
            }
          },
          "required": [
            "text"
          ]
        },
      }
    }
  ]
,
  model="gpt-4o-mini",
)

import requests

import re
def parse_llm_output(output):
    # Use regex to find the Description and Detail sections
    description_match = re.search(r'Description:\s*(.*?)\s*(?=Detail:|$)', output, re.DOTALL)
    detail_match = re.search(r'Detail:\s*(.*)', output, re.DOTALL)
    
    # Extract and clean the matched content
    description = description_match.group(1).strip() if description_match else ""
    detail = detail_match.group(1).strip() if detail_match else ""
    print("description: ")
    print(description)
    print("detail: ")
    print(detail)
    return description, detail

def new_memory(text):
    print("New Memory Function Called")
    # Fetch all memories from the API
    memories_response = requests.get('http://127.0.0.1:5000/memories')
    memories = memories_response.json()

    # Format the existing memories for the system prompt
    memories_str = "\n".join([f"{memory['id']}: {memory['description']}" for memory in memories])

    # Initial prompt to decide whether to create or update a memory
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"We have a db that stores memory of past conversation. You will be given a new memory that needs to be stored in the db. Create a new memory or choose to update an existing memory if relevant related memory already exists. Existing Memories:\n{memories_str}\nTo create a new memory, output only this: 'create_memory'. To update an existing memory, output only this: 'update_memory:<id>'."},
            {"role": "user", "content": f"{text}"}
        ]
    )

    response = completion.choices[0].message.content
    print("response: ")
    print(response)

    if response.startswith('update_memory:'):
        # Extract the memory ID to update
        memory_id = int(response.split(':')[1])

        # Fetch the existing memory details
        existing_memory_response = requests.get(f'http://127.0.0.1:5000/memory/{memory_id}')
        existing_memory = existing_memory_response.json()

        # Ask the model to update the existing memory's description and detail
        update_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": f"We have a db that stores memory of past conversation. The db comtains short description that acts like a index for the detailed memory. Existing memory details:\nDescription: {existing_memory['description']}\nDetail: {existing_memory['detail']}\n\nPlease update the existing memory to include the new information. The new information is given by the user thus can over write old memory even if contrary. Also, detail does not need to be very big, just what user has told. In your response provide description as: 'Description: <new_description>' and detail as: 'Detail: <new_detail>'."},
                {"role": "user", "content": f"{text}"}
            ]
        )

        update_response = update_completion.choices[0].message.content
        print('update_response: ')
        print(update_response)
        # update_data = update_response.split('\n')
        # updated_description = update_data[0]
        # updated_detail = update_data[1]
        updated_description, updated_detail = parse_llm_output(update_response)
        print("updated_description: ")  
        print(updated_description)
        print("updated_detail: ")
        print(updated_detail)

        # Call the update_memory API
        update_response = requests.put(
            f'http://127.0.0.1:5000/memory/{memory_id}',
            json={'description': updated_description, 'detail': updated_detail}
        )
        # Assuming update_response.json() returns a JSON string
        json_string = update_response.json()

        # Convert JSON string to Python dictionary
        # dict_obj = json_string

        # print('dict: ')
        # print(dict_obj)
        # print(f"{dict_obj['message']}")
        # print(f"Message: {json_string['message']}")
        # return f"Convo ended with status: {update_response.json()}"
        return f"{json_string['message']}"

    elif response == 'create_memory':
        # Ask the model to create a new memory's description and detail
        create_completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "We have a db that stores memory of past conversation. The db contains a short description that acts like an index for the detailed memory. Create a new memory with a description and detail.  Also, detail does not need to be very big, just what user has told.  In your response provide description as: 'Description: <new_description>' and detail as: 'Detail: <new_detail>'."},
                {"role": "user", "content": f"{text}"}
            ]
        )
    
        create_response = create_completion.choices[0].message.content
        print(create_response)
        # create_data = create_response.split('\n', 1)  # Split into two parts: description and detail
        # new_description = create_data[0]
        # new_detail = create_data[1]
        new_description, new_detail = parse_llm_output(create_response)
    
        # Call the store_memory API
        store_response = requests.post(
            'http://127.0.0.1:5000/store_memory',
            json={'description': new_description, 'detail': new_detail}
        )
        json_string = store_response.json()
        return f"{json_string['message']}"
        # return f"Convo ended with status: {store_response.json()}"

    else:
        return {'error': 'Invalid response from model'}

    
def use_memory(text):
    print("Use Memory Function Called")
    # Step 1: Call API to get all memories
    try:
        all_memories_response = requests.get("http://127.0.0.1:5000/memories")
        all_memories_response.raise_for_status()
        all_memories = all_memories_response.json()  # Assuming the response is in JSON format
    except requests.RequestException as e:
        return {'error': f"Failed to retrieve memories: {str(e)}"}

    # Step 2: Format memories as id.description
    formatted_memories = "\n".join([f"{memory['id']}. {memory['description']}" for memory in all_memories])
    print(f"formatted_memories: {formatted_memories}")
    # Step 3: Send all memories to the model
    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": f"We have a db that stores memory of past conversation. You will be given a query that requires memory to answer. You need to find the most relevant memory to answer the query. All Existing Memories:{formatted_memories}.. Provide the id of the memory that you think is most relevant to the query. If no relevant memory exists, respond with an appropriate message. Response with only the id or the message."},
            {"role": "user", "content": text}
        ]
    )
    print(completion.choices[0].message.content)
    response_content = completion.choices[0].message.content.strip()
    print("response_content: ")
    print(response_content)
    # Step 4: Get the model's response, which should be an id
    response_id = completion.choices[0].message.content.strip()
    print("response_id: ")
    print(response_id)
    if response_content.isdigit():
      # Step 5: Filter the memory using the id
      selected_memory = next((memory for memory in all_memories if memory['id'] == int(response_id)), None)
      print("selected_memory: ")
      print(selected_memory)
      if not selected_memory:
        return {'error': f"No memory found with id {response_id}"}
      # Step 6: Call the API again with both description and detail to ask the model to answer the query
      detailed_memory = selected_memory  # We already have the detailed memory from the initial API call

      # Step 7: Ask the model to answer the query using the detailed memory
      final_completion = client.chat.completions.create(
          model="gpt-4o-mini",
          messages=[
              {"role": "system", "content": f"We have a db that stores memory of past conversation. Use the following memory from db to answer the query given by user: {detailed_memory['description']} {detailed_memory['detail']}"},
              {"role": "user", "content": text}
          ]
      )

      final_response = final_completion.choices[0].message.content
      print("response: ")
      print(final_response)
      return final_response
    else:
      # If the response is not a number, return the model's output directly
      print("response_message: ")
      print(response_content)
      return response_content
# Example usage
thread = client.beta.threads.create()

def get_response(prompt):
    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=prompt
    )
    return message


thread = client.beta.threads.create()

import time
def wait_on_run(run):
    while run.status == "queued" or run.status == "in_progress":
        run = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id,
        )
        
        time.sleep(0.5)
    return run

def get_response(prompt):
    message = client.beta.threads.messages.create(
    thread_id=thread.id,
    role="user",
    content=prompt
    )

    run = client.beta.threads.runs.create_and_poll(
    thread_id=thread.id,
    assistant_id=assistant.id,
    )

    import json
    if run.status == 'completed': 
        messages = client.beta.threads.messages.list(
            thread_id=thread.id
        )
        print(messages)
        if messages.data:  # Check if there are any messages
                last_message = messages.data[0]  # Get the last message
                if last_message.content:  # Check if the message has content
                    text_content_block = last_message.content[0]  # Get the first TextContentBlock
                    message_text = text_content_block.text.value  # Extract the text value
                    print(message_text)
                    return message_text
                else:
                    print("The last message has no content.")
                    print(messages)
        else:
            print(run.status)
    elif run.status == "requires_action":
        function_map = {
          'use_memory': use_memory,
          'new_memory': new_memory,
        }
        tool_call = run.required_action.submit_tool_outputs.tool_calls[0]
        name = tool_call.function.name
        arguments = json.loads(tool_call.function.arguments)

        print("Waiting for custom Function:", name)
        print("Function arguments:")
        print(arguments)
        # reply = name(**arguments)
        # return reply

        # Retrieve the actual function from the function_map
        function_to_call = function_map.get(name)
        if function_to_call is None:
            raise ValueError(f"Function '{name}' is not defined in function_map")

        # Call the function with the provided arguments
        # reply = function_to_call(**arguments)
        # Call the function with the provided arguments
        function_response = function_to_call(**arguments)

        run = client.beta.threads.runs.submit_tool_outputs(
            thread_id=thread.id,
            run_id=run.id,
            tool_outputs=[
                {
                    "tool_call_id": tool_call.id,
                    "output": "done. function response:" + function_response,
                }
            ],
        )
        # import time
        # time.sleep(3)
        # # Inform the function response to the thread model
        # client.beta.threads.messages.create(
        #     thread_id=thread.id,
        #     role="assistant",
        #     content=function_response
        # )
        #  # Wait for the thread's response
        # run = client.beta.threads.runs.create_and_poll(
        #     thread_id=thread.id,
        #     assistant_id=assistant.id,
        # )
        # if run.status == 'completed':
        #     messages = client.beta.threads.messages.list(
        #         thread_id=thread.id
        #     )
        #     if messages.data:  # Check if there are any messages
        #         last_message = messages.data[0]  # Get the last message
        #         if last_message.content:  # Check if the message has content
        #             text_content_block = last_message.content[0]  # Get the first TextContentBlock
        #             message_text = text_content_block.text.value  # Extract the text value
        #             return message_text
        #         else:
        #             print("The last message has no content.")
        #             print(messages)
        #     else:
        #         print(run.status)
        # else:
        #     print(run.status)
        #     print(run)
        #     return "Some Error occurred in the LLM run. Sorry for the inconvenience."
        run = wait_on_run(run)
        return function_response
    else:
        print(run.status)
        print(run)
        return "Some Error occured in the LLM run. Sorry for the inconvenience."