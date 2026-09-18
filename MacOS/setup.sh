#!/usr/bin/env zsh
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
DOTFILES_DIR="$REPO_DIR/dotfiles"

# ── Homebrew ──────────────────────────────────────────────────────────────────
if ! command -v brew &>/dev/null; then
  echo "Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  eval "$(/opt/homebrew/bin/brew shellenv)"
fi

# ── Oh My Zsh ─────────────────────────────────────────────────────────────────
if [[ ! -d "$HOME/.oh-my-zsh" ]]; then
  echo "Installing Oh My Zsh..."
  RUNZSH=no CHSH=no sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
fi

# ── CLI tools ─────────────────────────────────────────────────────────────────
brew install --quiet \
  zsh-autosuggestions zsh-syntax-highlighting \
  gh \
  kubernetes-cli kubelogin \
  gardenctl-v2 gardenlogin \
  k9s \
  btop \
  trivy \
  shellcheck \
  ollama \
  herdr \
  pwgen \
  deno \
  kubie \
  exiftool \
  ffmpeg

# ── Casks ─────────────────────────────────────────────────────────────────────
brew install --quiet --cask \
  docker-desktop \
  font-hack-nerd-font \
  gcloud-cli \
  rustdesk

# ── omlx (local MLX inference server for Apple Silicon) ───────────────────────
if ! command -v omlx &>/dev/null && [[ ! -d "$HOME/.omlx" ]]; then
  brew tap jundot/omlx https://github.com/jundot/omlx
  brew install --quiet jundot/omlx/omlx
fi

# ── VSCode extensions ─────────────────────────────────────────────────────────
if command -v code &>/dev/null; then
  code --install-extension anthropic.claude-code --force
  code --install-extension github.vscode-github-actions --force
  code --install-extension ms-python.python --force
  code --install-extension ms-python.vscode-pylance --force
  code --install-extension ms-python.debugpy --force
fi

# ── Zsh plugins (symlink brew-installed plugins into OMZ) ─────────────────────
ZSH_CUSTOM="${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}"

mkdir -p "$ZSH_CUSTOM/plugins/zsh-autosuggestions"
ln -sf "$(brew --prefix)/share/zsh-autosuggestions/zsh-autosuggestions.zsh" \
  "$ZSH_CUSTOM/plugins/zsh-autosuggestions/zsh-autosuggestions.plugin.zsh"

mkdir -p "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting"
ln -sf "$(brew --prefix)/share/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh" \
  "$ZSH_CUSTOM/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.plugin.zsh"

# ── KCP CLI ───────────────────────────────────────────────────────────────────
# Not on Homebrew — download from internal release page.
# Check https://github.tools.sap/kyma/kcp-cli/releases for the latest version.
if ! command -v kcp &>/dev/null || [[ "$(command -v kcp)" != "/usr/local/bin/kcp" ]]; then
  echo "Installing kcp CLI..."
  KCP_VERSION="1.13.0"
  curl -fsSL "https://github.tools.sap/kyma/kcp-cli/releases/download/v${KCP_VERSION}/kcp-darwin-arm64-${KCP_VERSION}" \
    -o /usr/local/bin/kcp
  chmod +x /usr/local/bin/kcp
fi

# ── Dotfiles ──────────────────────────────────────────────────────────────────
echo "Symlinking dotfiles..."

ln -sf "$DOTFILES_DIR/.zshrc"               "$HOME/.zshrc"
ln -sf "$DOTFILES_DIR/.gitconfig"           "$HOME/.gitconfig"
ln -sf "$DOTFILES_DIR/.gitconfig-personal"  "$HOME/.gitconfig-personal"

mkdir -p "$HOME/.config/git"
ln -sf "$DOTFILES_DIR/.gitignore_global" "$HOME/.config/git/ignore"

mkdir -p "$HOME/.config/gh"
ln -sf "$DOTFILES_DIR/gh_config.yml"     "$HOME/.config/gh/config.yml"

mkdir -p "$HOME/Library/KeyBindings"
ln -sf "$DOTFILES_DIR/DefaultKeyBinding.dict" "$HOME/Library/KeyBindings/DefaultKeyBinding.dict"

echo ""
echo "NOTE: Place your kubeconfig files in ~/.kube/configs/ — kubie scans this directory."
echo "      kcp config files go in ~/.kcp/ and are selected via kcpenv <dev|stage|prod|us50|cn40>."

# ── macOS defaults ────────────────────────────────────────────────────────────
# Use F1–F12 as standard function keys (Fn modifier needed for volume/brightness/etc.)
defaults write NSGlobalDomain com.apple.keyboard.fnState -bool true

# ── Photos-Manipulations Python dependencies ──────────────────────────────────
# Required by scripts in MacOS/Photos-Manipulations/
# ocrmac wraps Apple's Vision framework (Live Text) — macOS 12+ only.
pip3 install --quiet --upgrade \
  Pillow \
  numpy \
  ocrmac

echo ""
echo "Done. Run: source ~/.zshrc" or reload the shell.
