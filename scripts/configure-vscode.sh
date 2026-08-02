#!/bin/bash

mkdir -p .vscode

# Create settings.json with the specified configuration
cat > .vscode/settings.json << 'EOF'
{
  "js/ts.tsdk.path": "frontend/node_modules/typescript/lib",

  "editor.defaultFormatter": "oxc.oxc-vscode",
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.fixAll.oxc": "explicit",
    "source.format.oxc": "explicit"
  },

  "[javascript]": { "editor.defaultFormatter": "oxc.oxc-vscode" },
  "[javascriptreact]": { "editor.defaultFormatter": "oxc.oxc-vscode" },
  "[typescript]": { "editor.defaultFormatter": "oxc.oxc-vscode" },
  "[typescriptreact]": { "editor.defaultFormatter": "oxc.oxc-vscode" },
  "[json]": { "editor.defaultFormatter": "oxc.oxc-vscode" },
  "[jsonc]": { "editor.defaultFormatter": "oxc.oxc-vscode" }
}
EOF

echo "VSCode settings configured successfully ☄️"

# Common recommended extensions
code --install-extension oxc.oxc-vscode
code --install-extension bradlc.vscode-tailwindcss
code --install-extension ms-python.python
code --install-extension charliermarsh.ruff

echo "Recommended VSCode extensions installed! 🐸"