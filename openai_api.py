import os

import openai
from dotenv import load_dotenv

from data.init_prompts import *

# Load environment variables from the .env file
load_dotenv()

# Set the OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")


def openai_request(language):
    """
    Handles the conversation between two characters by making requests to the OpenAI API.

    Args:
        language (str): The language of the conversation. "EN" for English, "ES" for Spanish.

    Returns:
        dict: A dictionary with two lists, "sender" and "receiver", containing the messages from each character.
    """
    # Define a function to remove line breaks from a list of strings
    def delete_line_break(lista):
        """
        Removes line breaks and character names from a list of strings.

        Args:
            lista (list): The list of strings to process.

        Returns:
            list: The list of strings without line breaks and character names.
        """
        for i in range(len(lista)):
            lista[i] = lista[i].replace("\n", "")
            lista[i] = lista[i].replace("Kyle:", "")
            lista[i] = lista[i].replace("Cartman:", "")
        return lista

    # Define a function to make requests to the OpenAI API with retries
    def openai_connection(user_prompt):
        """
        Makes a request to the OpenAI API with retries.

        Args:
            user_prompt (str): The prompt to send to the OpenAI API.

        Returns:
            str: The response from the OpenAI API, or None if the request fails after maximum retries.
        """
        MAX_TRIES = 3
        tries = 0
        while tries < MAX_TRIES:
            try:
                # Try to make the request to the OpenAI API
                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": user_prompt}],
                    max_tokens=256
                )
                # Return the assistant's reply text
                return completion.choices[0].message.content
            except Exception as e:
                # If an error occurs, print an error message and retry
                tries += 1
                print(
                    "Error request to OpenAI. Trying again ({}/{}): {}".format(
                        tries, MAX_TRIES, e
                    )
                )
        # If the maximum number of retries is reached and the request still fails, return None
        return None

    if language == "ES":
        prompt_receiver = (
            description_ES_b + situation_ES_b
        )  # Initial prompt for the receiver in Spanish
        prompt_sender = (
            description_ES_a + situation_ES_a
        )  # Initial prompt for the sender in Spanish
        sender_list = [
            "Hola chico Slytherin, como estas?"
        ]  # Initial response from the sender in Spanish
    else:
        prompt_receiver = (
            description_EN_b + situation_EN_b
        )  # Initial prompt for the receiver in English
        prompt_sender = (
            description_EN_a + situation_EN_a
        )  # Initial prompt for the sender in English
        sender_list = [
            "Hello Slytherin boy, how are you?"
        ]  # Initial response from the sender in English

    itera = 0  # Initialize the variables needed for the conversation
    openai_iterations = int(os.getenv("OPENAI_NUMBER_ITERATIONS"))
    receiver_list = []
    # Carry out the conversation using requests to the OpenAI API
    while itera < openai_iterations:
        # Generate the receiver's response
        response_receiver = openai_connection(prompt_receiver)
        if response_receiver is None:
            print("Failed to get response from OpenAI. Stopping conversation.")
            break
        # Add the receiver's response to the sender's prompt
        prompt_sender = prompt_sender + ("\nKyle: " + response_receiver + "\n")
        prompt_receiver = prompt_receiver + ("\nKyle: " + response_receiver + "\n")
        # Add the receiver's response to the list of receiver's responses
        receiver_list.append(response_receiver)

        # Generate the sender's response based on the receiver's response
        response_sender = openai_connection(response_receiver)
        if response_sender is None:
            print("Failed to get response from OpenAI. Stopping conversation.")
            break
        prompt_receiver = prompt_receiver + ("\nCartman: " + response_sender + "\n")
        prompt_sender = prompt_sender + ("\nCartman: " + response_sender + "\n")
        # Add the sender's response to the list of sender's responses
        sender_list.append(response_sender)
        itera += 1
    # Return a dictionary with the sender's and receiver's response lists without line breaks
    return {
        "sender": delete_line_break(sender_list),
        "receiver": delete_line_break(receiver_list),
    }
