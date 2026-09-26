import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
import uuid


REPO = Path(__file__).resolve().parents[1]
CONFIGS = {
    ".zshrc": ".zshrc",
    ".p10k.zsh": ".p10k.zsh",
    ".config/tmux/tmux.conf": ".config/tmux/tmux.conf",
    ".tmux.conf": ".config/tmux/tmux.conf",
}


class InstallTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="dotfiles-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home with spaces"
        self.home.mkdir()
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.env = {
            "HOME": str(self.home),
            "PATH": f"{self.bin}:/usr/bin:/bin",
            "TERM": "xterm-256color",
            "LANG": "C.UTF-8",
        }
        self.executable("uname", '#!/bin/sh\nprintf "%s\\n" "${TEST_OS:-Darwin}"\n')
        self.executable("brew", '#!/bin/sh\nprintf "%s\\n" "$*" >> "$HOME/brew.log"\n')
        self.executable("git", '''#!/bin/bash
set -eu
printf '%s\\n' "$*" >> "$HOME/git.log"
if [[ "${FAIL_GIT:-}" == 1 ]]; then exit 1; fi
if [[ "$1" == clone ]]; then
  mkdir -p "${@: -1}"
elif [[ "$1" == -C && "$3" == checkout ]]; then
  case "${2##*/}" in
    .oh-my-zsh) entry=oh-my-zsh.sh ;;
    powerlevel10k) entry=powerlevel10k.zsh-theme ;;
    zsh-autosuggestions) entry=zsh-autosuggestions.plugin.zsh ;;
    zsh-syntax-highlighting) entry=zsh-syntax-highlighting.plugin.zsh ;;
    tpm) entry=tpm ;;
    tmux-sensible) entry=sensible.tmux ;;
    tmux-resurrect) entry=resurrect.tmux ;;
    tmux-continuum) entry=continuum.tmux ;;
    tmux-yank) entry=yank.tmux ;;
    vim-tmux-navigator) entry=vim-tmux-navigator.tmux ;;
    *) exit 1 ;;
  esac
  [[ "${@: -1}" =~ ^[0-9a-f]{40}$ ]]
  printf '#!/bin/sh\\ntrue\\n' > "$2/$entry"
  chmod +x "$2/$entry"
else
  exit 1
fi
''')

    def executable(self, name, content):
        path = self.bin / name
        path.write_text(content)
        path.chmod(0o755)

    def install(self, success=True, **env):
        result = subprocess.run(
            ["/bin/bash", str(REPO / "install.sh")],
            env={**self.env, **env}, text=True, capture_output=True,
        )
        if success:
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        else:
            self.assertNotEqual(result.returncode, 0)
        return result

    def assert_links(self):
        for target, source in CONFIGS.items():
            path = self.home / target
            self.assertTrue(path.is_symlink(), target)
            self.assertEqual(path.resolve(), REPO / source)

    def test_fresh_install_and_rerun(self):
        self.install()
        self.assert_links()
        log = (self.home / "git.log").read_text()
        self.assertEqual(len(log.splitlines()), 20)
        self.install()
        self.assert_links()
        self.assertEqual((self.home / "git.log").read_text(), log)
        self.assertFalse((self.home / ".dotfiles-backups").exists())

    def test_backups_preserve_existing_files(self):
        for target in CONFIGS:
            path = self.home / target
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(f"original {target}")
        self.install()
        self.assert_links()
        backups = list((self.home / ".dotfiles-backups").iterdir())
        self.assertEqual(len(backups), 1)
        for target in CONFIGS:
            self.assertEqual((backups[0] / target).read_text(), f"original {target}")
        self.assertEqual(backups[0].stat().st_mode & 0o777, 0o700)
        self.install()
        self.assertEqual(list((self.home / ".dotfiles-backups").iterdir()), backups)

    def test_symlinks_and_their_targets_are_preserved(self):
        original = self.home / "original-zshrc"
        original.write_text("keep me")
        (self.home / ".zshrc").symlink_to(original)
        missing = self.home / "missing-p10k"
        (self.home / ".p10k.zsh").symlink_to(missing)
        self.install()
        self.assert_links()
        backup = next((self.home / ".dotfiles-backups").iterdir())
        self.assertEqual(os.readlink(backup / ".zshrc"), str(original))
        self.assertEqual(os.readlink(backup / ".p10k.zsh"), str(missing))
        self.assertEqual(original.read_text(), "keep me")
        self.assertFalse(missing.exists())

    def test_refuses_linux_without_changes(self):
        self.install(success=False, TEST_OS="Linux")
        self.assertEqual(list(self.home.iterdir()), [])

    def test_refuses_custom_config_locations(self):
        self.install(success=False, ZDOTDIR=str(self.home / "custom-zsh"))
        self.install(success=False, XDG_CONFIG_HOME=str(self.home / "custom-config"))
        self.assertEqual(list(self.home.iterdir()), [])

    def test_download_failure_does_not_replace_configs(self):
        original = self.home / ".zshrc"
        original.write_text("keep me")
        self.install(success=False, FAIL_GIT="1")
        self.assertEqual(original.read_text(), "keep me")
        self.assertFalse(original.is_symlink())
        self.assertFalse((self.home / ".dotfiles-backups").exists())

    def test_incomplete_dependency_is_not_overwritten(self):
        existing = self.home / ".oh-my-zsh"
        existing.mkdir()
        (existing / "personal-file").write_text("keep me")
        self.install(success=False)
        self.assertEqual((existing / "personal-file").read_text(), "keep me")
        self.assertFalse((self.home / ".zshrc").exists())

    @unittest.skipUnless(shutil.which("zsh"), "zsh unavailable")
    def test_zsh_without_optional_tools(self):
        self.install()
        (self.home / ".zshrc.local").write_text("export DOTFILES_LOCAL_LOADED=yes\n")
        command = 'source "$HOME/.zshrc"; [[ $ZSH_THEME == powerlevel10k/powerlevel10k && ${plugins[*]} == "git zsh-syntax-highlighting zsh-autosuggestions" && $POWERLEVEL9K_MODE == ascii && $DOTFILES_LOCAL_LOADED == yes ]]'
        result = subprocess.run(
            [shutil.which("zsh"), "-f", "-c", command],
            env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(result.stderr, "")

    @unittest.skipUnless(shutil.which("tmux"), "tmux unavailable")
    def test_tmux_configuration_in_isolated_server(self):
        self.install()
        socket = f"dotfiles-test-{uuid.uuid4().hex}"
        base = [shutil.which("tmux"), "-L", socket]
        self.addCleanup(lambda: subprocess.run(
            base + ["kill-server"], env=self.env, capture_output=True,
        ))
        result = subprocess.run(
            base + ["-f", str(self.home / ".tmux.conf"), "new-session", "-d", "-s", "verify", "/bin/sleep 60"],
            env=self.env, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        for option, expected in (("mouse", "on"), ("base-index", "1"), ("status-right", ""), ("status-justify", "centre")):
            result = subprocess.run(
                base + ["show-options", "-gv", option],
                env=self.env, text=True, capture_output=True, check=True,
            )
            self.assertEqual(result.stdout.strip(), expected)


if __name__ == "__main__":
    unittest.main()
