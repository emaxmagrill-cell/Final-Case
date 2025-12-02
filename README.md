# 1) Executive Summary

**Problem:**
The goal was to create a website that outlines the fantasy football leaderboards for each season. It has extra features to sort the players which would be shown in leaderboards allowing the view to sort by position and year. The leaderboard was created mainly to display this seasons player's fantasy football ranking in clear concise way to help people influence fantasy trades allow using to make better decisions and understand the value of their players better.

**Solution:** 
The website is structured with serveral options on the left side of the screen allowing the user to choose which information to load from the dataframe. The user has the option to choose between which year and which player group to display the leaderboard. This is done using the nflverse python extention which has a multitude of nfl datasets and this website utilitizes the nfl fantasy leaderboard which the service provides.

# 2) System Overview

**Course Concept(s):**
The main course concept used was a flask app in order to calculate the final fantasy leaderboard. The website utilizes four python files. The main python file is the App.py which utilitizes the flask app to run the website and calls the other three python files to configure and calculate the fantasy score boards.

**Architecture Diagram:** 
![Architecture Diagram](/assets/architecture.png)

**Data/Models/Services:**
The data is coming from a github repository called NFL verse ([Link](https://nflverse.nflverse.com/))

The data is being pulled from the nflverse repository using the nflreadpy python library on the during the use of the website.

# 3) How to Run (Local)

The website is ran using a docker container. Using these commands below to run the website:

```bash
docker build -t final_project:latest .

chmod +x run.sh

./run.sh
```

# 4) Design Decisions

The flask app was chosen for this project as it would be perfect for building a lightweight web app. A fastapi app was considered for the web app however a flask app would stil be capable of running this web application. It is also much simplier to set up a flask app and within this course I have gained more experience using the flask app. If this app is expanded to include more player stats then I may consider using fastapi app however there is not much room for growth for the app so the flask app should be fine for the continued deployment of this app. For the deployment of the app, I choose a docker container instead of a kubernetes deployment. This app does not need any additional containers to run so I decided against using the more complicated kubernetes deployment in favor a simpler docker single image deployment.

# 5) Results & Evaluation

The website is over all very successful. The app is deployable with a clear leaderboard of the fantasy football players by the most points scored in the full PPR fantasy football. However there are some limitations. I do not believe that the database that is being used is the most accurate source of information and some of the statistics are inaccurate. A future change I would like to make is to change the database used and find a more accurate source of information. I would also like to improve the efficiency of the app as currently the app is not efficient enough to run on the service provided by render.com.

**Example Screenshots:**

![Leaderboard Example 1](/assets/example01.png)

![Leaderboard Example 2](/assets/example02.png)

# 6) Links

**GitHub Repo:** [link](https://github.com/emaxmagrill-cell/Final-Case)
**Public Cloud App (optional):** [link](https://fantasy-football-leaderboard.onrender.com/)
