#FAUbot

###About
Faubot is an automated program that scrapes data from various FAU-related sources and shares them with [the FAU subreddit](https://reddit.com/r/FAU).
It will benefit the FAU community by providing a convenient forum for discovering and discussing FAU-related news and events.

This project originated as a class project for CEN4010, Principles of Software Engineering at Florida Atlantic University,
and it is maintained by some of the original developers. 

###Getting Started

####Initial Setup
1. Install [Python 3.5](https://www.python.org/downloads/release/python-350/).
2. If using Windows, [Add Python to your Path environment variable](http://stackoverflow.com/a/17176423), replacing `C:\Python27` with the location where you installed Python (most likely `C:\Python35`).
3. From the project folder, run `python -m pip install -r requirements.txt`.
4. If you don't have one, create a new Reddit account. Otherwise, decide which existing account you'd like to use.

####Preparing Your Reddit Account for Development
1. Copy `praw_example.ini` into a new file named `praw.ini`. Make sure it is saved in the same directory as `praw_example.ini`.
2. Change the first line of `praw.ini` from saying `[FAUbot]` to saying `[YourRedditAccountName]`, e.g. if I'm using 
   the account /u/jpfau, I would change the first line in `praw.ini` to say `[jpfau]`.
3. Follow [these instructions](http://praw.readthedocs.io/en/stable/pages/oauth.html) for registering a new app on Reddit.
   Don't worry about running any of the code on that page. Just take note of your new client ID and secret ID after creating the app.
4. Paste your client ID and secret ID into `praw.ini`.
5. From the command line, run the script account_register.py like this:
   `python account_register.py -a YourRedditAccountName`
   Make sure you replace `YourRedditAccountName` with the same user name from step 2.
6. A browser window will open with a non-existent web page. Copy [the code in the URL's query string](http://praw.readthedocs.io/en/stable/_images/CodeUrl.png),
   and paste it into the terminal where your script is running. The prompt should say `Enter Code:`.
7. When the script completes, a new refresh token should be saved in `praw.ini`. Verify that the token is there.

###Running the program
1. `praw.ini` specifies which bots will run. The value of `bot_class_name` is a comma-separated list of
   class names, all of which should be subclasses of `RedditBot` (see `bots.py`). 
2. From the command line, navigate to the project directory.
3. From *inside* the FAUbot directory, start the program with:
   `python .`

**Note:** There is a known issue that the project cannot be run from outside the project directory, e.g. `python ./FAUbot`.
      I think it's an issue with PRAW assuming that `praw.ini` is always in the current working directory, which is
      why for now you have to be inside the project directory to run it. 


###Contributing
This project is now taking pull requests! I'll try to be good about using the "Issues" page to document 
known bugs and desired features.