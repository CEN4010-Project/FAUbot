# FAUbot

To make this run:

1. Follow the instructions in docstring.io for installing Python.
2. From the project folder, run `pip install -r requirements.txt`
3. Copy your `praw_example.ini` file into a new file named `praw.ini`
4. Log into FAUbot's Reddit account
5. Follow [these instructions](http://praw.readthedocs.io/en/stable/pages/oauth.html#a-step-by-step-oauth-guide) for finding the client ID and client secret ID on [Reddit's app preferences page.](https://www.reddit.com/prefs/apps/)
6. Ask your group leader for the refresh token, and paste it in `praw.ini`. This will let the bot sign into Reddit automatically, no matter who is running it.
7. Verify your refresh token is stored in `praw.ini`.
8. From the project directory, run `python bots.py`.

## Taiga info

* User stories correspond to entire features of the program.
* Within the user story, individual tasks may be created and assigned to people.
* Stories and tasks have unique ID numbers associated with them. It started with #1, and it increments.
* You can also specify in a task/story how long you think it should take to complete it.


## Workflow

Here is how you should begin working on any task or bug fix.

1. If the task or story hasn't been created yet, create them. 
2. Put the new story/task in the "Ready" state.
3. In your local git repository (on your machine, not the remote repository), create a new branch from master (or from another branch if necessary):
   
    `git checkout -b your-new-branch-name`
   
    This command will create the new branch and immediately switch to it. 

4. On your very first commit, your commit message may include the Taiga command to move your story/task to a new state,
    
    ```bash
	git commit -m "TG-2 #in-progress This is a unique description of what I did in this commmit"
	```
   
    This will take the Taiga item with ID #2 and move it to the "In Progress" state. 
   You don't have to add the Taiga stuff as long as you move the item manually in Taiga.
5. Work on your code as normal. Make frequent commits with descriptive commit messages.

6. On your very last commit, you may include the Taiga command to move your task/story to QA (peer review).
   
    ```bash
	git commit -m "TG-2 #ready-for-test This is a unique description of my last commit"
	```
   
    **Note:** Just because the state is called "Ready for Test" doesn't mean you shouldn't test your code *before* opening a PR.
7. Push your progress to the remote branch.
   
   ```bash
   git push origin your-new-branch-name
   ```
8. On Github, use the UI to navigate to your new branch.
9. Use the UI to open a new pull request.
10. Other team members should pull your branch to their own computer and test your code.
   They also should read the code and leave comments with questions and feedback.
11. If the reviewers say your code needs more work, go back to step 5.
12. Once all reviewers approve your pull request, use the Github UI to merge your new branch with the branch you original branched from.
13. In Taiga, mark your task as Done. 
14. If all the tasks in a story are Done, move the story to Closed. 

## General info about creating tasks and stories
* Anyone can create a story or task, and anyone can assign a task to another user.
* For example, if you work primarily on the back-end and you discover a UI bug, 
  you should create a new task within the relevant story and assign it to whomever is responsible for the UI.
* Ideally we'll always put new stories in the backlog, and each week or two we will take
  some stories out of the backlog and work on them. We should try to avoid creating new stories 
  after we've already decided what to work on for the week (or two), but it's not terrible if it happens.
* In-depth discussions regarding features, tasks, or bugs should be done in the relevant story's comment section.

