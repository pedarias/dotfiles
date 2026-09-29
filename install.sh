#!/bin/bash
set -euo pipefail

if [[ "$(uname -s)" != Darwin ]]; then
  printf '%s\n' 'Este instalador é para macOS. Nenhuma configuração foi alterada.' >&2
  exit 1
fi

if [[ "$EUID" -eq 0 ]]; then
  printf '%s\n' 'Execute como seu usuário, sem sudo.' >&2
  exit 1
fi

if [[ "${ZDOTDIR:-$HOME}" != "$HOME" || "${XDG_CONFIG_HOME:-$HOME/.config}" != "$HOME/.config" ]]; then
  printf '%s\n' 'Este instalador usa ~/.zshrc e ~/.config/tmux. ZDOTDIR/XDG_CONFIG_HOME personalizados não são suportados.' >&2
  exit 1
fi

if ! command -v brew >/dev/null 2>&1; then
  for brew_bin in /opt/homebrew/bin/brew /usr/local/bin/brew; do
    if [[ -x "$brew_bin" ]]; then
      eval "$("$brew_bin" shellenv)"
      break
    fi
  done
fi

if ! command -v brew >/dev/null 2>&1; then
  printf '%s\n' 'Instale o Homebrew (https://brew.sh) e execute novamente: bash install.sh' >&2
  exit 1
fi

repo_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
backup_dir="$HOME/.dotfiles-backups/$(date +%Y%m%d-%H%M%S)-$$"

for formula in tmux zoxide fzf; do
  brew list --versions "$formula" >/dev/null 2>&1 || brew install "$formula"
done

clone_pinned() {
  local repository="$1" revision="$2" destination="$3" entrypoint="$4"
  if [[ -f "$destination/$entrypoint" ]]; then
    printf 'Mantendo instalação existente: %s\n' "$destination"
    return
  fi
  if [[ -e "$destination" || -L "$destination" ]]; then
    printf 'O caminho já existe, mas está incompleto: %s. Revise-o antes de tentar novamente.\n' "$destination" >&2
    exit 1
  fi
  mkdir -p "$(dirname -- "$destination")"
  git clone --filter=blob:none --no-checkout "https://github.com/$repository.git" "$destination"
  git -C "$destination" checkout --quiet --detach "$revision"
  test -f "$destination/$entrypoint"
}

clone_pinned ohmyzsh/ohmyzsh d42209f2afa8ec3e6971e5b4695ff27f9d5670d2 "$HOME/.oh-my-zsh" oh-my-zsh.sh
clone_pinned romkatv/powerlevel10k 36f3045d69d1ba402db09d09eb12b42eebe0fa3b "$HOME/.oh-my-zsh/custom/themes/powerlevel10k" powerlevel10k.zsh-theme
clone_pinned zsh-users/zsh-autosuggestions 85919cd1ffa7d2d5412f6d3fe437ebdbeeec4fc5 "$HOME/.oh-my-zsh/custom/plugins/zsh-autosuggestions" zsh-autosuggestions.plugin.zsh
clone_pinned zsh-users/zsh-syntax-highlighting 5eb677bb0fa9a3e60f0eff031dc13926e093df92 "$HOME/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting" zsh-syntax-highlighting.plugin.zsh
clone_pinned tmux-plugins/tpm 99469c4a9b1ccf77fade25842dc7bafbc8ce9946 "$HOME/.tmux/plugins/tpm" tpm
clone_pinned tmux-plugins/tmux-sensible 25cb91f42d020f675bb0a2ce3fbd3a5d96119efa "$HOME/.tmux/plugins/tmux-sensible" sensible.tmux
clone_pinned tmux-plugins/tmux-resurrect cff343cf9e81983d3da0c8562b01616f12e8d548 "$HOME/.tmux/plugins/tmux-resurrect" resurrect.tmux
clone_pinned tmux-plugins/tmux-continuum 0698e8f4b17d6454c71bf5212895ec055c578da0 "$HOME/.tmux/plugins/tmux-continuum" continuum.tmux
clone_pinned tmux-plugins/tmux-yank acfd36e4fcba99f8310a7dfb432111c242fe7392 "$HOME/.tmux/plugins/tmux-yank" yank.tmux
clone_pinned christoomey/vim-tmux-navigator c45243dc1f32ac6bcf6068e5300f3b2b237e576a "$HOME/.tmux/plugins/vim-tmux-navigator" vim-tmux-navigator.tmux

link_config() {
  local source="$1" target="$HOME/$2"
  if [[ "$source" -ef "$target" ]]; then
    return
  fi
  if [[ -e "$target" || -L "$target" ]]; then
    (umask 077; mkdir -p "$(dirname -- "$backup_dir/$2")")
    mv "$target" "$backup_dir/$2"
    printf 'Backup: %s\n' "$backup_dir/$2"
  fi
  mkdir -p "$(dirname -- "$target")"
  ln -s "$source" "$target"
}

link_config "$repo_dir/.p10k.zsh" .p10k.zsh
link_config "$repo_dir/.zshrc" .zshrc
link_config "$repo_dir/.config/tmux/tmux.conf" .config/tmux/tmux.conf
link_config "$repo_dir/.config/tmux/tmux.conf" .tmux.conf
link_config "$repo_dir/.config/ghostty/config.ghostty" .config/ghostty/config.ghostty

printf '\n%s\n' 'Pronto. Abra uma nova janela do terminal ou execute: exec zsh -l' 'Depois execute: tmux' 'Mantenha esta pasta: as configurações apontam para ela por links simbólicos.' 'Instalações existentes dos plugins foram preservadas; instalações novas usam as versões do Linux.' 'Servidores tmux já abertos não foram alterados. Para recarregar, use Ctrl-b e depois r.'
