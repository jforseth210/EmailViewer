"""
A simple imap client and email viewer
"""
from getpass import getpass
import imaplib
import email
from email import policy
import os
import socket
import dotenv
import html2text
dotenv.load_dotenv()


def main():
    """
    The main program, logs in, and views emails
    until stopped with CTRL+D or CTRL+C
    """
    print("Welcome to email viewer!")
    print("Here, you can view all of your email in a convient terminal interface.")
    print("Press CTRL+D or CTRL+C to exit the program")

    # Read or prompt for credentials
    url, port, username, password = get_credentials()

    # Connect to the server
    imap = connect(url, port)

    # Use a context manager to ensure the connection is closed
    with imap:
        # Log into the server
        login(imap, username, password)
        # List folders
        status, folders = imap.list()

        # Convert to a list of strings
        folders = parse_folders(folders)

        while True:
            # Print folders to the console
            print_folders(folders)

            # Prompt the user to select a folder
            selected_folder = select_folder(folders)

            # Read the messages in the folder
            print("Loading messages...")
            messages = get_messages_from_folder(imap, selected_folder)
            if len(messages) == 0:
                continue
            print()
            print(f"Emails in {selected_folder}:")
            print()

            # Print out index, sender, and subject line
            print_message_summaries(messages)

            # Prompt the user to select a message
            selected_message = select_message(messages)

            # Get the body text of the selected message
            selected_message_body = selected_message.get_body(
                preferencelist=("plain", "html"))

            # Clear the screen
            # https://stackoverflow.com/questions/517970/how-can-i-clear-the-interpreter-console
            print("\033[H\033[J", end="")

            if selected_message_body.get_content_type() == 'text/html':
                # Attempt to handle HTML only emails somewhat gracefully
                text_maker = html2text.HTML2Text()
                text_maker.ignore_anchors = False
                text_maker.ignore_tables = True
                print(text_maker.handle(selected_message_body.get_content()))
            else:
                # Print plaintext emails to the console
                print(selected_message_body.get_content())


def get_credentials():
    """
    Retrieve credentials from environment variables or by prompting the user

    NOTE: The environment variable names aren't great in that they're likely to
    have name collisoons with other programs, but since this is mainly inteded
    to work with dotenv, that shouldn't be a problem.
    """

    # Get url
    url = os.getenv("URL", None)
    if not url:
        url = input("Enter IMAP URL: ")

    # Get port
    port = os.getenv("PORT", None)
    while not port:
        port = None
        port_input = input("Enter IMAP PORT (default=993): ")

        if port_input == "":
            # Default to 993
            port = 993
        else:
            try:
                # Attempt to parse as an integer
                port = int(port_input)
            except ValueError:
                # Handle user not entering an integer
                print(f"{port_input} is not an integer")

        if port is not None and (port < 0 or port > 65535):
            # It's an int, but not a valid port number
            print(f"{port} is not a valid port")
            port = None

    # Get username
    username = os.getenv("USERNAME", None)
    if not username:
        username = input("Enter username: ")

    # Get password
    password = os.getenv("PASSWORD", None)
    if not password:
        password = getpass(
            "Enter password (password will not be shown on screen): ")
    return url, port, username, password


def connect(url, port):
    """
    Make a connection to an IMAP server.
    If connection fails, reprompt the user.
    Continue prompting until a conection is established
    or the program is exited.
    """

    imap = None
    while imap is None:
        try:
            # Try to connect
            imap = imaplib.IMAP4_SSL(url, port=port)
            return imap
        except socket.gaierror:
            print(f"Unable to connect to server. Is {url} the correct URL?")
            url = input("Enter IMAP URL: ")


def login(imap, username, password):
    """
    Try to login into the imap server.
    If login fails, reprompt the user.
    Continue prompting until login is successful or the program is exited.
    """

    while True:
        try:
            # Try logging in
            imap.login(username, password)
            return
        except imaplib.IMAP4.error:
            # Login failed, reprompt
            print("Login failed, please try again:")
            username = input("Enter username: ")
            password = getpass(
                "Enter password (password will not be shown on screen): ")


def get_messages_from_folder(imap, folder):
    """
    Retrieve all messages in the given folder
    and return a list of email message objects

    NOTE: The given folder must be an existing
    folder in the imap server.
    """
    # Select the folder
    imap.select(folder)
    messages = []
    # Get a list of messages from the the server
    typ, data = imap.search(None, 'ALL')
    for num in data[0].split():
        # Fetch message
        typ, data = imap.fetch(num, '(RFC822)')
        # Parse message
        msg = email.message_from_bytes(
            data[0][1], policy=policy.default)

        # Add it to the list
        messages.append(msg)
    return messages


def print_message_summaries(messages):
    """
    Prints a summary of each message
    """
    # Print out the index, sender, and subject of each message
    for i, msg in enumerate(messages):
        print(f"{i+1}: {msg['from'].split(' <')[0]}: {msg['subject']}")


def select_message(messages):
    """
    Prompt the user to select a message
    """
    while True:
        # Prompt the user to choose a message
        selected_message_input = input(
            "Please choose a message: ")

        try:
            # Try to convert the input to an integer
            selected_message_index = int(selected_message_input)-1
        except ValueError:
            # The user did not enter an integer
            print(f"{selected_message_input} is not a message number")
            continue

        # Make sure the index is valid
        if selected_message_input < 0 or selected_message_index >= len(messages):
            print(f"{selected_message_input} is not a message number")
            continue

        # Return the selected message
        return messages[selected_message_index]


def get_inbox_index(folders):
    """
    Look for an inbox folder and return
    its index (starting at 1).

    Return None if not found.
    """
    inbox_index = None
    for i, folder in enumerate(folders):
        # Is folder inbox?
        if folder.lower() == "inbox":
            # Get index
            inbox_index = i+1
    return inbox_index


def parse_folders(folders):
    """
    Get folder names as strings
    """
    parsed_folders = []
    for i, folder in enumerate(folders):
        folder = folder.decode("utf-8")
        folder = folder.split('"')
        folder = folder[-2]
        parsed_folders.append(folder)
    return parsed_folders


def print_folders(folders):
    for i, folder in enumerate(folders):
        # Print folder index and name
        print(f"{i+1}: {folder}")


def select_folder(folders):
    """
    Prompt the user to select a folder,
    continue prompting until a valid folder is selected
    """
    # Attempt to find the inbox
    inbox_index = get_inbox_index(folders)
    while True:
        # Inbox index if found, otherwise, just use index 1
        selected_folder_input = input(
            "Please choose a folder "
            f"[default={inbox_index if inbox_index else 1}]: ")

        # Should we use the default folder?
        if selected_folder_input == "":
            # Use the default
            return folders[inbox_index-1]

        # Did the user enter a folder name?
        for folder in folders:
            if selected_folder_input.lower() == folder.lower():
                # The user entered the name of this folder
                return folder

        # Did the user enter a folder number?
        selected_folder_index = None
        try:
            # Try to convert it to a number
            selected_folder_index = int(selected_folder_input)-1
        except ValueError:
            # It's not a number
            print(f"{selected_folder_input} is not a valid folder name or number")
            continue

        # It's a number, is it valid?
        if selected_folder_index < 0 or selected_folder_index >= len(folders):
            # Nope, not a valid index
            print(f"{selected_folder_index} is not a valid folder number")
            continue

        # It's a valid folder index, return the folder
        return folders[selected_folder_index]


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt, imaplib.IMAP4.abort):
        # Handle close
        print()
        print("Goodbye!")
