#FAUbot

###About
Faubot is an automated program that scrapes data from various FAU-related sources and shares them with [the FAU subreddit](https://reddit.com/r/FAU).
It will benefit the FAU community by providing a convenient forum for discovering and discussing FAU-related news and events.

###Contributing
Because this is a group project for a class, we currently accept code changes from group members only.

####How to Run:

1. Install [Python 3.5](https://www.python.org/downloads/release/python-350/).
2. [Add Python to your Path environment variable](http://stackoverflow.com/a/17176423), replacing `C:\Python27` with the location where you installed Python (most likely `C:\Python35`).
3. From the project folder, run `python -m pip install -r requirements.txt`.
4. If you already have the `praw.ini` file, go to step 9.
5. Copy your `praw_example.ini` file into a new file named `praw.ini`.
6. Log into FAUbot's Reddit account. Ask a group member if you don't have the password.
7. Follow [these instructions](http://praw.readthedocs.io/en/stable/pages/oauth.html#a-step-by-step-oauth-guide) for finding the client ID and client secret ID on [Reddit's app preferences page.](https://www.reddit.com/prefs/apps/)
8. Ask a group member for the refresh token, and paste it in `praw.ini`. This will let the bot sign into Reddit automatically, no matter who is running it.
9. Verify your refresh token is stored in `praw.ini`.
10. From the project directory, run `python .`. That is the 'python' command, a space, and a period.
