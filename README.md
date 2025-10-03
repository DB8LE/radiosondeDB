# RadiosondeDB

A tool for logging radiosonde flights received with radiosonde_auto_rx.

> [!IMPORTANT]
> This project is still in early development. Breaking changes are being made constantly.

## Installing

First off, only linux is supported. The expected setup is having RSDB installed on the same server as autorx, which probably runs linux. Other operating systems might work, but they are completely untested.

RadiosondeDB provides multiple apps. They can all be installed with essentially the same commands, with just the name of the app differing.

### AutoRX setup

These configuration options should be set in radiosonde_auto_rx:

1. Ensure `payload_summary_enabled` is set to true
2. Set `ozi_update_rate` to zero

#### Optional: Modify code to include extra data

If you want data like the rs41 mainboard or firmware version, you need to slightly modify the code.
If you're running an older version (before v1.8.0), you will also need to do this to get pressure and XDATA values.
In the file `radiosonde_auto_rx/auto_rx/autorx/ozimux.py`, look for the list `EXTRA_FIELDS` and ensure the list contains these strings: `"pressure", "aux", "rs41_mainboard", "rs41_mainboard_fw"`.

### Initial setup

These commands need to be run once regardless of the app that will be installed.

```bash
# Start in whichever directory you want to install to

# Clone repository and enter
git clone https://github.com/DB8LE/radiosondeDB.git
cd radiosonde

# Create venv and enter it
python3 -m venv venv
source ./venv/bin/activate

# Install dependencies
# Note: optionally, systemctl journal support can be enabled by running
# `pip install .[journal]` instead. Journal support requires the dependency python3-systemd
pip install .

# Create config file based on example
cp config.example.toml config.toml

# Edit the config with your favourite editor
nano config.toml
```

### Application installation

After the initial setup, that's most of it. All that is left is adding a systemd service
to keep RSDB running. If you don't use systemd, you will have to figure this part out for yourselves.

These instructions are for the archiver, if you want to install a different app, just replace all
occurences of the word "archiver" with your app in the following commands.

```bash
# Start in radiosondeDB install directory

# Copy provided systemd service
sudo cp ./deploy/rsdb-archiver.service /etc/systemd/system/

# Replace all occurences of "<your_user>" with actual user
sudo sed -i "s/<your_user>/$(whoami)/g" /etc/systemd/system/rsdb-archiver.service

# Reload systemd and enable service
sudo systemctl daemon-reload
sudo systemctl enable rsdb-archiver.service

# Start!
sudo systemctl start rsdb-archiver.service
```

## Updating

> [!CAUTION]
> Breaking changes to the database or other parts of the program makes updating require more steps. When these do happen, a guide on how to update will be added to this file.

```bash
# Start in radiosondeDB install directory

# Pull from github (optionally stash using `git stash` first if you've made changes to the code)
git pull

# Activate venv
source ./venv/bin/activate

# Install using pip (as with installation, optionally add [journal] for systemctl journal support)
pip install .

# Compare new config.example.toml file and old config.toml file, and check for new/changed configuration options.
# RSDB will not start with mismatched configuration keys between config.example.toml and config.toml.

# If using systemd service, restart it
sudo systemctl restart rsdb-*
```

## Launchsites

Optionally, the positions of known radiosonde launch sites can be configured by the user to be displayed on the map.

To configure these, simply create a a file named `launchsites.txt` in the project root directory, and edit it to set your
launch sites in this format:

`<Name>,<Latitude>,<Longitude>` (seperated by newlines)
