import requests
import json

local_server_url = "http://localhost:11434/api/chat"

def store_message(message, role="user", history=[], inplace=False):
    """
    Summary: This function is used to add new messages to the chat history.
    
    Args:
        message (str): The message to be stored in the chat history.
        role (str, optional): Defaults to "user".
        history (list, optional): Should be a list containing the chat history. Defaults to [].
        inplace (bool, optional): Set to true if you want to change the original list. Defaults to False.

    Returns:
        (list): Returns the chat history with the new message added.
    """
    
    if inplace:
        history.append({"role": role, "content": message})
        return history
    else:
        new_history = history.copy()
        new_history.append({"role": role, "content": message})
        return new_history

def groq_hidden_chat(client, system_message, message, seed):
    """
    Summary: This function is used to send a message to GROQ chat server and get advice from it.

    Args:
        client (Groq): add a groq object containing the api key.
        system_message (str): system message for the hidden chat server.
        message (str): message from the user.
        seed (int): add a seed for reproducibility.

    Returns:
        (str): Returns the advice from the GROQ chat server.
    """
    
    # Add the the string "User message: " to the beginning of the user message helps the model understand that the message is from the user.
    message["content"] = "User message: " + message["content"]
    
    # Send the message to the GROQ chat server
    chat_completion = client.chat.completions.create(    
        messages=[system_message, message],
        model="llama3-8b-8192",
        seed=seed,
    )
    
    return chat_completion.choices[0].message.content

def hidden_chat(system_message, message, seed):
    # This function is used to give extra information to the chat server, but it is not shown to the user. 
    # And the response is not shown to the user.
    
    """
    Summary: This function is used to send a message to the local chat server and get advice from it.
    
    Args:
        system_message (str): system message for the hidden chat server.
        message (str): message from the user.
        seed (int): add a seed for reproducibility.

    Returns:
        (str): Returns the advice from the local chat server.
    """
    
    url = local_server_url
    
    message["content"] = "User message: " + message["content"]
    
    data = {
        "model": "llama3",
        "messages": [system_message, message],
        "stream": False,
        "options": {
            "seed": seed,
        }
    }
    
    response = requests.post(url, data=json.dumps(data))
    return response.json()["message"]["content"]

def contact_chat_server(message, seed, advice=" ", history_list=[]):
    
    """
    summary: 
        This function sends the user message to the local hidden chat server. It takes the response from the server and sends it as an advice to the chat server, 
        together with the user message. It then streams back the respons. When the streaming is done, the response is added to the chat history. 
        The advice is left out of the chat history.
        
    Args:
        message (str): The message from the user.
        seed (int): The seed for reproducibility.
        advice (str, optional): The advice from the hidden chat server. Defaults to " ".
        history_list (list, optional): The chat history. Defaults to [].

    Returns:
        (Generator): Returns a generator that yields the response from the chat server.

    Yields:
        (str): The message from the server.
    """
    
    url = local_server_url

    # Add the advice to the temp chat history just before adding the last message
    if(advice != " "):
        temp_history = store_message(advice, role="user", history=history_list, inplace=False)
        
    # Add the user message to the temporary chat history, after the advice
    temp_history = store_message(message, role="user", history=temp_history, inplace=False)

    # Add the user message to the chat history, without the advice
    history_list = store_message(message, role="user", history=history_list, inplace=True)
    
    data = {
        "model": "llama3",
        # use ternary operator to switch between chat_history and temp_history
        "messages": temp_history,
        "stream": True,
        "options": {
            "seed": seed # Add ability to change seed in frontend later 240430
        }
    }
    
    # Send the message to the local chat server
    response = requests.post(url, data=json.dumps(data), stream=True)

    # Define a generator to stream the response
    def generate():
        final_message = ""
        for line in response.iter_lines(decode_unicode=True):
            if line:
                data = json.loads(line)
                message = data["message"]["content"].strip('"')
                done = data["done"]
                if message:  # Only update last_message if message is not empty
                    final_message += message
                if done:
                    store_message(final_message, role="assistant", history=history_list, inplace=True)
                yield message

    return generate

def contact_chat_server_groq(client, message, seed, advice=None, history_list=[]):
    
    """
    summary:
    This function sends the user message to the GROQ hidden chat server. It takes the response from the server and sends it as an advice to the chat server, 
    together with the user message. It add the respons to the chat history. 
    The advice is left out of the chat history.

    Returns:
        (str): The message from the server.
    """
    
    # Add the advice to the temp chat history just before adding the last message
    temp_history = store_message(advice, role="user", history=history_list, inplace=False)
        
    # Add the user message to the temporary chat history, after the advice
    temp_history = store_message(message, role="user", history=temp_history, inplace=False)
    
    # Add the user message to the chat history, without the advice
    history_list = store_message(message, role="user", history=history_list, inplace=True)    
        
    # Send the message to the GROQ chat server
    chat_completion = client.chat.completions.create(    
        messages=temp_history,
        model="llama3-8b-8192",
        seed=seed,
    )
        
    # Get the response from the GROQ chat server
    final_message = chat_completion.choices[0].message.content
    
    # Store the response in the chat history
    store_message(final_message, role="assistant", history=history_list, inplace=True)
        
    return final_message