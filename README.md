# dotfiles

My Zsh, Powerlevel10k and tmux setup, with a one-command macOS installer.

## Install (macOS)

Requires [Homebrew](https://brew.sh).

```bash
brew install gh
gh auth login --hostname github.com --git-protocol https --web
gh repo clone pedarias/dotfiles "$HOME/dotfiles"
```

Or, if you already have Git with SSH access to GitHub:

```bash
git clone git@github.com:pedarias/dotfiles.git "$HOME/dotfiles"
```

Then run the installer:

```bash
bash "$HOME/dotfiles/install.sh"
```

Open a new terminal and run `tmux`. Files it replaces are backed up to `~/.dotfiles-backups/`.

## What's inside

- **Zsh + Oh My Zsh**: Zsh is the shell; Oh My Zsh adds git aliases, autosuggestions and syntax highlighting.
- **Powerlevel10k**: a fast prompt that shows your directory, git status, and how long slow commands took.
- **tmux**: keeps your terminal work alive and organized. Detach, come back later, and everything is where you left it.

## tmux in 30 seconds

A **session** is a workspace, **windows** are its tabs, and **panes** split a window into side-by-side terminals.

![tmux demo](demo/tmux.gif)

The prefix is `Ctrl+b`: press it, release, then press the key.

| Keys | Action |
|---|---|
| `tmux new -s work` / `tmux a` | Start a session / reattach |
| `Ctrl+b d` | Detach (it keeps running) |
| `Ctrl+b s` | Switch sessions |
| `Ctrl+b c` | New window |
| `Ctrl+b n` / `p` / `1-9` | Next / previous / jump to window |
| `Ctrl+b \|` / `-` | Split side by side / top-bottom |
| `Ctrl+b h j k l` | Move between panes |
| `Ctrl+b H J K L` | Resize pane |
| `Ctrl+b z` | Zoom pane (toggle) |
| `Ctrl+b x` | Close pane |
| `Ctrl+b [` → `v` → `y` | Scroll, select, copy |
| `Ctrl+b r` | Reload config |

**Extras:** `Ctrl+h/j/k/l` moves between panes without the prefix. Sessions are saved automatically and restored when tmux starts (`Ctrl+b Ctrl+s` / `Ctrl+b Ctrl+r` to save / restore by hand).

## Notes

- Keep `~/dotfiles` in place: your configs are symlinks into it.
- Put machine-specific settings in `~/.zshrc.local` (not versioned).
