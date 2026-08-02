# Global Coffee Match `☕️🌍`

_UCU x Fluxon Summer School 2026_

## Development

Before starting your work on this project, we need to do a couple of steps to set up your tooling.

This list will help you set up your machine for local development.

### Pre-requisites

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

### Local development setup

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

4. Start the project!

```shell
npm run dev
```

5. Go to http://localhost:5173/ to see the web app live!

6. Open the project in VSCode (if haven't yet)

```shell
code .
```

7. You should be all set! Now you can start contributing to the project! 🤘
