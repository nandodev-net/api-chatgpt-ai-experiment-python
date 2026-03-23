import os
import threading
import tkinter as tk
from itertools import count, cycle

import pyttsx3
from dotenv import load_dotenv
from PIL import Image, ImageTk

from data import test_dialogues
from openai_api import openai_request


# Custom Label class to display images and animated gifs
class ImageLabel(tk.Label):
    """
    A Label that displays images, and plays them if they are gifs.

    Attributes:
        frames (cycle): A cycle of frames if the image is a gif.
        delay (int): The delay between frames in milliseconds.
        paused (bool): Whether the animation is currently paused.
    """

    def load(self, im):
        """
        Loads an image or gif for display.

        Args:
            im (str or PIL.Image): A string filename or a PIL Image instance.

        Returns:
            None
        """
        if isinstance(im, str):
            im = Image.open(im)
        frames = []

        try:
            # If the image is a gif, iterate through its frames
            for i in count(1):
                frames.append(ImageTk.PhotoImage(im.copy()))
                im.seek(i)
        except EOFError:
            pass
        self.frames = cycle(frames)
        self.paused = False

        try:
            self.delay = im.info["duration"]
        except KeyError:
            self.delay = 100

        if len(frames) == 1:
            self.config(image=next(self.frames))
        else:
            self.next_frame()

    def unload(self):
        """
        Unloads the current image.
        """
        self.config(image=None)
        self.frames = None

    def pause(self):
        """Stops the gif animation on the current frame."""
        self.paused = True

    def resume(self):
        """Resumes the gif animation from where it was paused."""
        if self.paused:
            self.paused = False
            self.next_frame()

    def next_frame(self):
        """
        Displays the next frame of the gif.
        """
        if self.frames and not self.paused:
            self.config(image=next(self.frames))
            self.after(self.delay, self.next_frame)


class ChatInterface:
    """
    A class to handle the chat interface.

    Attributes:
        root (tk.Tk): The main window of the chat interface.
        engine (pyttsx3.Engine): The text-to-speech engine.
        voices (list): A list of available voices for the text-to-speech engine.
        face1_frame (tk.Frame): The frame for the first chat participant's image.
        face2_frame (tk.Frame): The frame for the second chat participant's image.
        face1_label (ImageLabel): The label to display the first participant's image.
        face2_label (ImageLabel): The label to display the second participant's image.
        dialogue_label (tk.Text): The text box to display the conversation.
    """

    def __init__(self, root, dialogue_a, dialogue_b):
        """
        Initializes the chat interface.

        Args:
            root (tk.Tk): The main window of the chat interface.
            dialogue_a (list): The list of messages from the first participant.
            dialogue_b (list): The list of messages from the second participant.

        Returns:
            None
        """
        self.root = root
        self.root.configure(bg="#101010")
        self.root.title("Chat Interface")

        # Initialize the text-to-speech engine
        self.engine = pyttsx3.init()
        # Get a list of available voices
        self.voices = self.engine.getProperty("voices")

        # Create the frames for the chat interface
        self.face1_frame = tk.Frame(self.root)
        self.face1_frame.grid(row=0, column=0, padx=10, pady=10)
        self.face2_frame = tk.Frame(self.root)
        self.face2_frame.grid(row=0, column=2, padx=10, pady=10)

        # Load GIFs paused and hidden — they appear when Start is pressed
        self.face1_label = ImageLabel(self.face1_frame)
        self.face1_label.load("assets/talk.gif")
        self.face1_label.pause()
        self.face1_label.grid(row=1, column=0, sticky="w")
        self.face1_frame.grid_remove()

        self.face2_label = ImageLabel(self.face2_frame)
        self.face2_label.load("assets/talk2.gif")
        self.face2_label.pause()
        self.face2_label.grid(row=1, column=1, sticky="e")
        self.face2_frame.grid_remove()

        # Create the text box for the conversation
        self.dialogue_label = tk.Text(
            self.root, height=20, width=50, bg="white", wrap="word", relief="flat"
        )
        self.dialogue_label.config(font=("Arial", 10), state="disabled")
        self.dialogue_label.grid(row=0, column=1, padx=10, pady=10)
        self.dialogue_label.configure(bg="#333")
        self.dialogue_label.configure(font=("Arial", 12), fg="white")

        # Start button — triggers the conversation when clicked
        self.start_button = tk.Button(
            self.root,
            text="Start",
            font=("Arial", 12, "bold"),
            bg="#444",
            fg="white",
            relief="flat",
            padx=20,
            pady=8,
            command=lambda: self.start_conversation(dialogue_a, dialogue_b),
        )
        self.start_button.grid(row=1, column=1, pady=10)

        # Set up the layout
        self.root.columnconfigure(0, weight=1)
        self.root.columnconfigure(1, weight=1)
        self.root.columnconfigure(2, weight=1)
        self.root.rowconfigure(0, weight=1)

    def start_conversation(self, dialogue_a, dialogue_b):
        """Shows the GIFs, disables the start button, and begins the dialogue."""
        self.face1_frame.grid()
        self.face2_frame.grid()
        self.start_button.config(state="disabled", text="Playing...")
        self.send_dialogue(True, dialogue_a, dialogue_b)

    # Method to animate the gifs
    def animate_gif(self, label, gif_path):
        """
        Animates a gif in the specified label.

        Args:
            label (ImageLabel): The label to display the gif.
            gif_path (str): The path to the gif file.

        Returns:
            None
        """
        label.load(gif_path)

    # Method to handle window closing
    def on_close(self):
        """
        Handles the window closing event.
        """
        self.root.quit()

    # Method to send the conversation messages
    def send_dialogue(self, is_you, dialogue_a, dialogue_b):
        """
        Sends the conversation messages between participants.

        Args:
            is_you (bool): Flag to indicate if the current message is from the user.
            dialogue_a (list): The list of messages from the first participant.
            dialogue_b (list): The list of messages from the second participant.

        Returns:
            None
        """
        # If it's the user's turn and there are messages to send
        if is_you and dialogue_a:
            message = dialogue_a.pop(0)
            voice = self.voices[language_voices[0]].id
            speaking_label = self.face1_label
            silent_label = self.face2_label
        # If it's the other person's turn and there are messages to send
        elif not is_you and dialogue_b:
            message = dialogue_b.pop(0)
            voice = self.voices[language_voices[1]].id
            speaking_label = self.face2_label
            silent_label = self.face1_label
        else:
            # End the conversation if there are no more messages
            return

        # Pause the silent participant and animate only the speaking one
        silent_label.pause()
        speaking_label.resume()

        self.print_message(is_you, message)

        # Run TTS in a background thread so the main thread (and GIF animations) keep running.
        # Once speech finishes, schedule the next turn from the main thread via root.after().
        def speak_and_continue():
            self.speak_message(voice, message)
            self.root.after(100, lambda: self.send_dialogue(not is_you, dialogue_a, dialogue_b))

        threading.Thread(target=speak_and_continue, daemon=True).start()

    # Method to display the messages in the text box
    def print_message(self, is_you, message):
        """
        Displays the messages in the text box.

        Args:
            is_you (bool): Flag to indicate if the current message is from the user.
            message (str): The message to display.

        Returns:
            None
        """
        self.dialogue_label.config(state="normal")
        if is_you:
            self.dialogue_label.insert("end", "Cartman: ", "you_tag")
        else:
            self.dialogue_label.insert("end", "Kyle: ", "other_tag")
        self.dialogue_label.insert("end", message + "\n")
        self.dialogue_label.config(state="disabled")
        self.dialogue_label.see("end")

    # Method to speak the messages out loud
    def speak_message(self, voice, message):
        """
        Speaks the messages out loud.

        Args:
            voice (str): The voice ID to use for speaking.
            message (str): The message to speak.

        Returns:
            None
        """
        self.engine.setProperty("voice", voice)
        self.engine.say(message)
        self.engine.runAndWait()


if __name__ == "__main__":

    load_dotenv()

    # Load the test dialogues if specified
    if os.getenv("TYPE_OF_INPUT") == "TEST":
        if os.getenv("LANGUAGE") == "EN":
            dialogue_a = test_dialogues.dialogue_a_EN
            dialogue_b = test_dialogues.dialogue_b_EN
            language_voices = [0, 1]
        else:
            dialogue_a = test_dialogues.dialogue_a_ES
            dialogue_b = test_dialogues.dialogue_b_ES
            language_voices = [0, 1]

    # Get the dialogues from OpenAI API
    else:
        print("Getting conversation from OpenAI...\n")
        if os.getenv("LANGUAGE") == "EN":
            print("requesting dialogue to openai.")
            dialogues = openai_request("EN")
            dialogue_a = dialogues["sender"]
            dialogue_b = dialogues["receiver"]
            language_voices = [0, 1]
        else:
            print("requesting dialogue to openai.")
            dialogues = openai_request("ES")
            dialogue_a = dialogues["sender"]
            dialogue_b = dialogues["receiver"]
            language_voices = [0, 1]

    # Create the main window and chat interface
    root = tk.Tk()
    chat_interface = ChatInterface(root, dialogue_a, dialogue_b)

    # Configure the text box tags for different speakers
    chat_interface.dialogue_label.tag_configure(
        "you_tag", foreground="red", font=("Arial", 10, "bold")
    )
    chat_interface.dialogue_label.tag_configure(
        "other_tag", foreground="green", font=("Arial", 10, "bold")
    )

    # Handle the window closing event
    root.protocol("WM_DELETE_WINDOW", chat_interface.on_close)
    root.mainloop()
