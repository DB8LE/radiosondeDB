# RadiosondeDB

A tool for logging radiosonde flights received with radiosonde_auto_rx.

## Installing

First off, only linux is supported. The expected setup is having RSDB installed on the same server as autorx, which probably runs linux. Other operating systems might work, but they are completely untested.

RadiosondeDB provides multiple apps. They can all be installed with essentially the same commands, with just the name of the app differing.

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
