# Deploying Gaal

This guide installs one private Gaal instance for one user on a systemd-based
Linux host. It follows the same shape as the current production deployment:
one Microsoft 365 mailbox, one work schedule, one SQLite database and one
private Telegram destination.

Gaal is not currently a hosted multi-user service or a container image. These
instructions assume the operator is comfortable administering a Linux server
and has root access.

## Before starting

The host needs:

- a supported 64-bit Linux distribution with systemd;
- Python 3.11 or later, including `venv` support;
- Git, `sudo` and outbound HTTPS access;
- enough persistent storage for the checkout, Python environment and small
  SQLite audit database;
- a stable clock and timezone data.

The operator needs:

- a Microsoft 365 work or school account with a mailbox;
- permission to register an application in Microsoft Entra, or help from the
  organisation's Entra administrator;
- an OpenAI API key with billing and usage limits configured;
- a private Telegram account and a bot created through BotFather;
- a full Git commit SHA from `main` whose GitHub CI run is green.

Do not create a Microsoft client secret. Gaal uses delegated device-code
authentication as the user, not application-only access.

## 1. Register the Microsoft application

In Microsoft Entra:

1. Register a new application for Gaal.
2. Choose the narrowest supported account type appropriate to the user. For an
   internal installation, this is normally the current organisational directory
   only.
3. Record the **Application (client) ID** and **Directory (tenant) ID**.
4. Under **Authentication**, enable public client flows so device-code sign-in
   is permitted.
5. Under **API permissions**, add Microsoft Graph delegated `Mail.Read`.
6. Do not add mail write, send or application permissions.

Tenant policy may require an administrator to approve even delegated
permissions. Gaal itself requires only read access to the signed-in user's mail.

## 2. Prepare Telegram

Create a bot with BotFather and retain the bot token. Open the new bot's private
chat and send it a message so Telegram creates an update for that conversation.

Use Telegram's `getUpdates` Bot API method to identify the numeric `chat.id` for
that private conversation. Treat both the bot token and chat ID as credentials:
do not paste them into an issue, commit, screenshot or shared shell history.

## 3. Choose the release

On a trusted workstation with the repository checked out:

```sh
git fetch origin main
git rev-parse origin/main
```

Copy the full 40-character SHA and confirm its GitHub Actions CI run passed on
Python 3.11 and 3.13. The examples below call this value `<release-sha>`.

## 4. Install the application

On the Linux host, install distribution packages as needed. For Debian or
Ubuntu this is typically:

```sh
apt update
apt install git python3 python3-venv sudo
```

Create the service account and machine-local directories:

```sh
useradd --system --create-home --home-dir /var/lib/gaal \
  --shell /usr/sbin/nologin gaal
install -d -o root -g gaal -m 0750 /etc/gaal
install -d -o gaal -g gaal -m 0750 /var/lib/gaal
```

Clone and select the verified release:

```sh
git clone https://github.com/breaoneill/Gaal.git /opt/gaal
git -C /opt/gaal switch --detach <release-sha>
chown -R root:root /opt/gaal
python3 -m venv /opt/gaal/.venv
/opt/gaal/.venv/bin/pip install --disable-pip-version-check \
  "/opt/gaal[microsoft365]"
```

Run the same verification used by the release process:

```sh
PYTHONPATH=/opt/gaal/src /opt/gaal/.venv/bin/python \
  -m unittest discover -s /opt/gaal/tests -q
/opt/gaal/.venv/bin/python -m compileall -q \
  /opt/gaal/src /opt/gaal/tests
/opt/gaal/.venv/bin/python -m pip check
```

## 5. Configure Gaal

Install the example as the machine configuration:

```sh
install -o root -g gaal -m 0640 \
  /opt/gaal/config/gaal.example.toml /etc/gaal/gaal.toml
sudoedit /etc/gaal/gaal.toml
```

Set:

- `[work]` to the user's real timezone, working days, start and finish times;
- `[microsoft365].client_id` and `tenant_id` to the Entra values;
- `[microsoft365].token_cache` to
  `~/.local/state/gaal/msal-cache.json`;
- `[reasoning].provider` to `openai`;
- `[reasoning].model` to the deliberately selected OpenAI model;
- `[reasoning].api_key_env` to `OPENAI_API_KEY`;
- the Telegram environment-variable names as shown in the example.

The supplied systemd timer and runner are fixed to Europe/London and Monday to
Thursday at 07:30. If the user's schedule differs, update both the application
configuration and the files in `deploy/systemd` before installing them. The
timer decides when to run; the application schedule decides which communication
window to read. They must agree.

`update-gaal` refreshes the supplied unit files during every release. A schedule
edited only under `/etc/systemd/system` will therefore be overwritten. Until
host-specific timer overrides are supported, schedule changes must be carried
in the verified release being deployed.

Create the restricted service environment:

```sh
install -o root -g gaal -m 0640 /dev/null /etc/gaal/gaal.env
sudoedit /etc/gaal/gaal.env
```

Its contents are:

```text
OPENAI_API_KEY=<openai-api-key>
TELEGRAM_BOT_TOKEN=<telegram-bot-token>
TELEGRAM_CHAT_ID=<private-chat-id>
```

Do not add quotes, shell commands or `export`. The file is parsed by systemd.
Check ownership and permissions without printing its contents:

```sh
stat /etc/gaal/gaal.toml /etc/gaal/gaal.env
```

Both files should be owned by `root`, grouped to `gaal`, and mode `0640`.

## 6. Authorise Microsoft 365

Run authentication as the same account that will run the service:

```sh
sudo -u gaal env HOME=/var/lib/gaal \
  /opt/gaal/.venv/bin/gaal auth-microsoft365 \
  --config /etc/gaal/gaal.toml
```

Open the displayed Microsoft device-login URL on a trusted device, enter the
short code and sign in as the mailbox user. Gaal writes the delegated token
cache beneath `/var/lib/gaal`; it does not print or commit the token.

## 7. Run without delivery

Perform the first mailbox and reasoning test without
`--deliver-telegram`:

```sh
sudo -u gaal env HOME=/var/lib/gaal sh -c '
  set -a
  . /etc/gaal/gaal.env
  set +a
  exec /opt/gaal/.venv/bin/gaal daily \
    --config /etc/gaal/gaal.toml \
    --microsoft365 \
    --date "$(TZ=Europe/London date +%F)" \
    --run-at "$(TZ=Europe/London date --iso-8601=seconds)" \
    --state /var/lib/gaal/gaal.db
'
```

Review the briefing in the terminal. Confirm the window, categories and opaque
references are plausible. The audit record must identify this as a dry run:

```sh
sudo -u gaal env HOME=/var/lib/gaal \
  /opt/gaal/.venv/bin/gaal last-run \
  --state /var/lib/gaal/gaal.db
```

Do not proceed merely because the command exited successfully; the output must
also be useful and appropriate for the mailbox.

## 8. Test Telegram deliberately

Repeat the dry-run command with `--deliver-telegram` appended. This is a real
external action. Confirm beforehand that `TELEGRAM_CHAT_ID` names the intended
private conversation.

Confirm one complete briefing arrives. Gaal refuses to redeliver the same
scheduled window and refuses to send an oversized briefing in partial chunks.

## 9. Install and enable the service

Install and validate the supplied units and release command:

```sh
install -o root -g root -m 0644 \
  /opt/gaal/deploy/systemd/gaal-daily.service \
  /etc/systemd/system/gaal-daily.service
install -o root -g root -m 0644 \
  /opt/gaal/deploy/systemd/gaal-daily.timer \
  /etc/systemd/system/gaal-daily.timer
install -o root -g root -m 0755 \
  /opt/gaal/deploy/systemd/update-gaal \
  /usr/local/sbin/update-gaal
systemd-analyze verify \
  /etc/systemd/system/gaal-daily.service \
  /etc/systemd/system/gaal-daily.timer
systemctl daemon-reload
```

The timer is persistent. On first activation, systemd may treat an earlier
07:30 run as missed and start it immediately. To establish the installation as
already caught up before enabling it, create its initial timestamp:

```sh
install -d -o root -g root -m 0755 /var/lib/systemd/timers
touch /var/lib/systemd/timers/stamp-gaal-daily.timer
systemctl enable --now gaal-daily.timer
```

Verify the next trigger rather than assuming local and UTC display times are
the same:

```sh
systemctl is-enabled gaal-daily.timer
systemctl is-active gaal-daily.timer
systemctl list-timers gaal-daily.timer --all
```

## 10. Verify the first unattended run

After the next scheduled time:

```sh
systemctl status gaal-daily.service --no-pager
journalctl -u gaal-daily.service --since today --no-pager
sudo -u gaal env HOME=/var/lib/gaal \
  /opt/gaal/.venv/bin/gaal last-run \
  --state /var/lib/gaal/gaal.db
```

Confirm that Telegram received one complete briefing and that the audit record
says delivery succeeded. A missing briefing is not proof of an empty mailbox;
it may be a failed schedule, source, reasoning or delivery stage.

Independent failure notification is not yet implemented. Until it is, the
operator must check the timer and service after deployment and investigate a
missing morning briefing.

## Releasing a verified commit

CI is automatic; production deployment is deliberate. After a commit on `main`
passes GitHub CI, deploy its full SHA from a trusted workstation:

```sh
ssh root@<gaal-host> update-gaal <full-commit-sha>
```

`update-gaal`:

1. fetches `origin/main`;
2. rejects commits that are not on that branch;
3. checks out the exact requested commit;
4. recreates the Python environment;
5. repeats tests, compilation and dependency checks;
6. validates and refreshes the systemd files;
7. restores the previous revision if any step fails.

It does not run or deliver a briefing during deployment.

## Rollback

Use the same command with an earlier full SHA that is still an ancestor of
`origin/main`:

```sh
ssh root@<gaal-host> update-gaal <earlier-full-commit-sha>
```

After either a release or rollback, verify the revision and timer:

```sh
git -C /opt/gaal rev-parse HEAD
systemctl is-active gaal-daily.timer
systemctl list-timers gaal-daily.timer --all
```

## Backup and rebuild

Code is recoverable from Git. Machine identity and operational continuity are
not. Securely back up:

- `/etc/gaal/gaal.toml`;
- `/etc/gaal/gaal.env` using encrypted secret storage;
- `/var/lib/gaal/gaal.db`;
- the Microsoft token cache under `/var/lib/gaal/.local/state/gaal`, if local
  policy permits it.

The database contains no message bodies, but it does contain operational and
hashed conversation state. Treat it as private.

To rebuild a lost host:

1. provision a new supported Linux host;
2. install the last known good full SHA using this guide;
3. restore configuration, secrets and SQLite state with their original owners
   and permissions;
4. restore the Microsoft token cache or repeat device-code authentication;
5. perform a dry run;
6. perform an explicit Telegram test only if it will not duplicate a briefing;
7. initialise and enable the timer;
8. verify the next unattended run.

## Never commit

Do not add any of the following to Git:

- OpenAI or Telegram credentials;
- Microsoft tokens or token caches;
- populated production configuration;
- SQLite state databases;
- mailbox contents, briefings or diagnostic captures containing messages;
- server private keys or backups of `/etc/gaal`.

If a secret is committed or exposed in logs, revoke and replace it. Removing it
from the latest file is not sufficient because Git history retains earlier
content.
