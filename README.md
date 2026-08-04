# Global Coffee Match `☕️🌍`

Welcome to the Fluxon x UCU Summer School 2026! 👋👋👋

This is a Bootcamp project template. It contains minimal web app setup and doesn't contain anything related to your actual project. You are going to be building your app on top of this template. Thus, please change anything in this repository at your will in order to build your cool project! Start with this README - replace this with your project's title and description!

Overall, this README file is here to help you understand what we're dealing with, set up your machine for development, and provide some useful materials for learning web technologies.

🚧🚧🚧 Make sure to change this file to make it yours! 🚧🚧🚧

## Running the app

This should be ran in different terminals. One terminal for db, one for backend, and one for the frontend.

To run and initialize the database:

```
docker compose up -d
# Then
cd backend && uv run python -m app.scripts.init_db
```

To run frontend, run:

```
cd frontend && npm run dev
```

To run backend, run:

```
cd backend && uv run uvicorn app.main:app --reload
```

## Development

Before starting your work on this project, we need to do a couple of steps to set up your tooling.

This list will help you set up your machine for local development.

### Local setup

Initial steps you might have already done during your study at UCU:

- You should have a GitHub account
- Install Git: https://github.com/git-guides/install-git
- Install a code editor or IDE, such as VSCode: https://code.visualstudio.com/Download
- Use a shell terminal (bash, zsh, whatever) during the development process. You're good if you're on Mac or Linux. For Windows, use Git for Windows or WSL: https://superuser.com/a/1763710

- Install Node.js 24: https://nodejs.org/en/download/.

  ```shell
  curl -fsSL https://fnm.vercel.app/install | sh
  fnm install 24
  ```

- Install uv for Python: https://docs.astral.sh/uv/getting-started/installation/.

  ```shell
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- Install Docker Desktop (used to run the local Postgres database): https://www.docker.com/products/docker-desktop/. After installing, make sure Docker Desktop is running before you start the backend.

Now, let's set up your machine for real development 👇

1. Clone this Git repository:

```shell
# 1. Copy Git repository URL: on the GitHub page of this repository, click the green `<> Code` button > `📋` button to the right of the repository url.
# https://github.com/FluxonApps/ucu-global-coffee-match.git

# 2. Find a place where you want this project to live at.
cd ~; mkdir -p Projects; cd Projects # If you don't have a better place to put this repo

# 3. Clone the repository.
git clone https://github.com/FluxonApps/ucu-global-coffee-match.git

# 4. Navigate into the repository folder.
cd ucu-global-coffee-match
```

2. Configure your editor. This will ensure the code looks great for everyone the same way 💅

   - if using VSCode / Cursor, open this repository's **root folder** and run `./scripts/configure-vscode.sh`.
   - if using any other IDE, start questioning your life decisions. Or just ask mentors for help 😇

3. Install frontend dependencies using NPM. We are using libraries and code that was already written by other devs.

```shell
cd frontend
npm install
```

4. Install backend dependencies using uv, then go back to the repo root.

```shell
cd backend
uv sync
cp .env.example .env
cd ..
```

5. Start the project! This project has three parts that need to run at the same time - the database, the backend, and the frontend.

```shell
# Start database. Only needs to be ran once.
make db

# Starts Python backend server.
make backend

# Starts React frontend on http://localhost:5173.
make frontend
```

`make db` only needs to be re-run if Docker isn't already running the database container - it's
safe to run again any time, it won't wipe your data. If you ever want to wipe the database and
start fresh with seed data, run `make db-clear`. To stop the database, run `make db-stop`.

6. Go to http://localhost:5173/ to see the web app live!

7. Open the project in VSCode (if haven't yet)

```shell
code .
```

8. You should be all set! Now you can start contributing to the project! 🤘

## Deployment

Hey, some of you might be interested in setting up the deployment of your team's app 👀🚀

You could do this manually, or via an automated GitHub Actions workflow. Just ask your mentor!

## Useful Materials

> Before you proceed with this section, **REMEMBER THERE ARE NO STUPID OR LAME QUESTIONS**. If you're feeling like you don't know something, this means there's room for improvement – so just say it out loud and your mentor or peers will help you! We're all here to learn something new ([even mentors!](https://github.com/user-attachments/assets/c0c34e3a-8c5b-4bd8-9a8e-41c66bacece5)), so let's actually have a great time together!!!

> No, seriously, if there's anything, no matter however "obvious" this thing feels to you, don't be shy asking about it. Otherwise we'll be sad a question died never seeing the world 🥀🥀🥀

Some useful links for learning stuff we're dealing with at Bootcamp:

Web basics, https://internetingishard.netlify.app/ - a GREAT website that can help you better understand HTML & CSS.

JavaScript: https://www.geeksforgeeks.org/introduction-to-javascript/, https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide/Introduction, ask mentor for more.

React.js: official guide https://react.dev/learn, short hints https://devhints.io/react.

FastAPI: official tutorial https://fastapi.tiangolo.com/tutorial/.

Git: cheat sheet https://training.github.com/downloads/github-git-cheat-sheet.pdf.

TailwindCSS: official documentation https://tailwindcss.com/docs/styling-with-utility-classes.

The above list is incomplete, so if you need anything - you know [whom](https://github.com/FluxonApps/ucu-summer-school-project-template/assets/86969397/f93ff07b-f70e-476d-9ed5-14f25d474a53) to ask 😊

**Good luck!**
