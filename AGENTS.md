# Project context

- Keep this repo simple: the user's existing Oh My Zsh, Powerlevel10k and tmux configuration, plus a macOS installer.
- `bash install.sh` requires macOS and Homebrew. Never run it against a real home directory during testing.
- New plugin installations use the revisions recorded from the source Linux machine. Existing plugin installations are preserved.
- The installer backs up replaced files under `~/.dotfiles-backups/` and creates symlinks to this checkout. Keep the checkout in place.
- Put machine-specific settings in `~/.zshrc.local`, outside version control. Do not import credentials, shell history or tmux session snapshots.
- Syntax checks: `bash -n install.sh`, `zsh -n .zshrc`, `zsh -n .p10k.zsh`.
- Tests: `python3 -m unittest discover -s tests -v`. Tests use temporary homes, fake Homebrew/Git downloads, and an isolated tmux server when available. They do not validate real macOS package installation or real plugin execution.
