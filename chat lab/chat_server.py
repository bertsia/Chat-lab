from flask import Flask, request, render_template, Response
import time
import functions.chat_functions as llm_functions
import os
from groq import Groq

# Set key for GROQ API
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY")
)

app = Flask(__name__)

# Servers to use
# 0 = Local server
# 0 = GROQ server
hidden_chat_server_use = 1
chat_server_use = 1

# Chat history is set to a default system message
chat_history = [
    {"role": "system", 
     "content": """
        Act as a character of thick skin. 
        Don't be intimidated by childish user behavior and hate speach. 
        Be the better person.
    """},
]

# Generate a random seed
seed = int(time.time())

# Home page
@app.route('/')
def home():
    return render_template('front_page.html')

# Web page for character with advisor
@app.route('/character_with_advisor')
def character_with_advisor_get():
    return render_template('character_with_advisor.html')

# Post method for character with advisor
@app.route('/character_with_advisor', methods=['POST'])
def character_with_advisor_post():
    
    # Get the message, sentiment and seed from the form
    message = request.form.get('message')
    sentiment = request.form.get('style')
    user_seed = request.form.get('seed')
    
    # Check if seed is set by the user
    if user_seed != "":
        seed = int(user_seed)
    
    # Set the sentiment for the advisor
    advisor_sentiment = sentiment
    
    # Hard coded message to the hidden chat server for now
    hidden_system_message = f"""
        You are the thought process of the assistant.
        Your job is to give the advice to assistant agent on how to make the conversation engaging and {advisor_sentiment}.
        Keep it short and simple.
        
        Example 1: 
            "User message: The user is rude. Like greeting the agent in a degrading way. 
            Advice to assistant agent: Try to deescalate by telling greeting back in {advisor_sentiment} sarcastic way."
        
        Example 2: 
            "User message: The sense of the message is dull. Like mundane hello only. 
            Advice to assistant agent: Make it interesting, in a {advisor_sentiment} way."
            
        Remeber to always tell the assistant agent that it is adviced to act in a {advisor_sentiment} way. Otherwise
        it may mistake the advice for a comment.
        
        Avoid: 
            "Good morning to you too.",
            
        Instead:
            "Advice to assistant agent: Greet back in a {advisor_sentiment} way. For example: 'Good morning to you too.'"
        """
    
    # Message objects to add to the chat history
    hidden_system_object = {"role": "system", "content": hidden_system_message}
    hidden_message = {"role": "user", "content": message}
    
    # Determine what hidden chat server to use, local or GROQ
    if hidden_chat_server_use == 0:
        # Advice from local server
        advice = llm_functions.hidden_chat(hidden_system_object, hidden_message, seed)
    elif hidden_chat_server_use == 1:
        # Advice from GROQ server for faster inference
        advice = llm_functions.groq_hidden_chat(client, hidden_system_object, hidden_message, seed)
    else:
        advice = " "
        
    # Determine what chat server to use, local or GROQ
    if chat_server_use == 0:
        # Contact local chat server
        generator = llm_functions.contact_chat_server(message, seed, advice, chat_history)
        return Response(generator(), content_type='text/event-stream')
    elif chat_server_use == 1:
        # Contact GROQ chat server
        final_message = llm_functions.contact_chat_server_groq(client, message, seed, advice, chat_history)
        
        return final_message


if __name__ == "__main__":
    app.run(port=5000, debug=True)