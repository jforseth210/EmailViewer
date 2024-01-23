# Email Viewer
This is a simple imap client written in python that allows you to view emails in the console. 

To install this program, you'll need [https://www.python.org](python) and [https://git-scm.com](git) installed.

1. Simply clone the repository using: 
```bash
git clone https://github.com/
```
2. Install the dependencies using: 
```bash
python -m venv venv
venv/bin/activate
pip install -r requirements.txt
```

3. Run the program using: 
```bash
python main.py
```

This program uses IMAP over SSL, which is supported by most email providers.
Some email providers may require you to set an "app specific password" or 
similar in order to log in. Check with your provider for exact login details.

You can also store your credentials in a `.env` file if you don't want to be prompted every time.
Simply create a file named .env and add your credentials as follows: 

```bash
URL=imap.example.com
USERNAME=you@example.com
PASSWORD=averysecurepassword
PORT=993
```

Once logged in, you'll be presented with a list of your email folders.
Enter the name or number of the folder you want to view. 

Email Viewer will begin loading your messages. For large folders, this may take a while.
Once complete, you can view your emails by entering the number of the message you want to view.

Features such as: 
- Marking emails as read/unread
- Deleting emails
- Archiving emails
- Sending emails

are not supported at this time.
