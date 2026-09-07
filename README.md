# configurations
Config files for various systems and apps

## MacOS

Bootstrap a new Mac with a single\* command:

```bash
git clone https://github.com/jacekon/configurations.git
cd configurations/MacOS
./setup.sh
```

**What it does:**
- Installs Homebrew and Oh My Zsh (if missing)
- Installs CLI tools: `gh`, `kubectl`, `kubelogin`, `gardenctl-v2`, `gardenlogin`, `k9s`, `btop`, `trivy`, `shellcheck`, `ollama`, `herdr`, `kubie`, `pwgen`, `deno`
- Installs casks: `docker-desktop`, `font-hack-nerd-font`, `gcloud-cli`, `rustdesk`
- Installs omlx (local MLX inference server for Apple Silicon)
- Installs VSCode extensions
- Wires up zsh plugins (autosuggestions, syntax highlighting, kubectl, gh, docker, gcloud, k9s, brew, deno)
- Symlinks dotfiles from this repo into `$HOME`

**Dotfiles managed:**
- `~/.zshrc` → `MacOS/dotfiles/.zshrc`
- `~/.gitconfig` → `MacOS/dotfiles/.gitconfig` (SAP email globally, personal email for `~/GH/jacekon/`)
- `~/.gitconfig-personal` → `MacOS/dotfiles/.gitconfig-personal`
- `~/.config/git/ignore` → `MacOS/dotfiles/.gitignore_global`
- `~/.config/gh/config.yml` → `MacOS/dotfiles/gh_config.yml`
- `~/Library/KeyBindings/DefaultKeyBinding.dict` → `MacOS/dotfiles/DefaultKeyBinding.dict` (Windows-style Home/End/PageUp keys)

**After running:**
- Edit dotfiles directly in the cloned repo — changes are live immediately since all are symlinked
- Place kubeconfig files in `~/.kube/configs/` — kubie scans this directory automatically
- Place kcp config files in `~/.kcp/` and switch environments with `kcpenv <dev|stage|prod|us50|cn40>`
- \*Manually do: Obsidian-Notes/Apple/The_New_File_Shortcut.md 

## PopOS / Ubuntu / NixOS

See the respective directories for numbered setup scripts.
