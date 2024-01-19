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
    print("Welcome to email viewer!")
    print("Here, you can view all of your email in a convient terminal interface.")
    print("Press CTRL+D or CTRL+C to exit the program")
    url, username, password = get_credentials()
    imap = connect(url)
    with imap:
        login(imap, username, password)
        status, folders = imap.list()
        folders = parse_folders(folders)
        while True:
            print_folders(folders)
            selected_folder = select_folder(folders)

            print("Loading messages...")
            messages = get_messages_from_folder(imap, selected_folder)

            print()
            print(f"Emails in {selected_folder}:")
            print()
            print_message_summaries(messages)
            selected_message = select_message(messages)
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
                print(selected_message_body.get_content())


def get_credentials():

    url = os.getenv("URL", None)
    if not url:
        url = input("Enter IMAP URL: ")

    username = os.getenv("USERNAME", None)
    if not username:
        username = input("Enter username: ")

    password = os.getenv("PASSWORD", None)
    if not password:
        password = getpass(
            "Enter password (password will not be shown on screen): ")
    return url, username, password


def connect(url):
    imap = None
    while imap is None:
        try:
            imap = imaplib.IMAP4_SSL(url)
            return imap
        except socket.gaierror:
            print(f"Unable to connect to server. Is {url} the correct URL?")
            url = input("Enter IMAP URL: ")


def login(imap, username, password):
    while True:
        try:
            imap.login(username, password)
            return
        except imaplib.IMAP4.error:
            print("Login failed, please try again:")
            username = input("Enter username: ")
            password = getpass(
                "Enter password (password will not be shown on screen): ")


def get_messages_from_folder(imap, folder):
    imap.select(folder)
    messages = []
    typ, data = imap.search(None, 'ALL')
    for num in data[0].split():
        typ, data = imap.fetch(num, '(RFC822)')
        msg = email.message_from_bytes(
            data[0][1], policy=policy.default)
        messages.append(msg)
    return messages


def print_message_summaries(messages):
    for i, msg in enumerate(messages):
        print(f"{i+1}: {msg['from'].split(' <')[0]}: {msg['subject']}")


def select_message(messages):
    while True:
        selected_message_input = input(
            "Please choose a message: ")

        try:
            selected_message = messages[int(selected_message_input)-1]
            return selected_message
        except ValueError:
            print(f"{selected_message_input} is not a message number")
        except IndexError:
            print(f"{selected_message_input} is not a message number")


def get_inbox_index(folders):
    inbox_index = None
    for i, folder in enumerate(folders):
        if folder.lower() == "inbox":
            inbox_index = i+1
    return inbox_index


def parse_folders(folders):
    parsed_folders = []
    for i, folder in enumerate(folders):
        folder = folder.decode("utf-8")
        folder = folder.split('"')
        folder = folder[-2]
        parsed_folders.append(folder)
    return parsed_folders


def print_folders(folders):
    for i, folder in enumerate(folders):
        print(f"{i+1}: {folder}")


def select_folder(folders):
    inbox_index = get_inbox_index(folders)
    while True:
        selected_folder_input = input(
            "Please choose a folder "
            f"[default={inbox_index if inbox_index else 1}]: ")

        if selected_folder_input == "":
            return folders[inbox_index-1]

        for folder in folders:
            if selected_folder_input.lower() == folder.lower():
                return folder

        try:
            selected_folder = folders[int(selected_folder_input)-1]
            return selected_folder
        except ValueError:
            print(f"{selected_folder_input} is not a folder name or number")
        except IndexError:
            print(f"{selected_folder_input} is not a valid folder number")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt, imaplib.IMAP4.abort):
        print()
        print("Goodbye!")
