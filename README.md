Build the image using the following command

To run: `python3 main.py`

The application will be accessible at http:127.0.0.1:5000.

**Setup EC2 Instance**

sudo apt-get update
sudo apt-get install python3-pip
sudo apt-get install emacs

# sudo ln -s /usr/bin/python3 /usr/bin/python
# sudo ln -s /usr/bin/pip3 /usr/bin/pip

mkdir code
cd code
git clone https://github.com/dennishorte/cube-legacy-online.git

pip3 install virtualenv
pip3 install virtualenvwrapper

# Add to .bashrc
export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3
export WORKON_HOME=$HOME/.virtualenvs
export VIRTUALENVWRAPPER_VIRTUALENV=~/.local/bin/virtualenv
source ~/.local/bin/virtualenvwrapper.sh

# Back to command line
cd ~
source .bashrc
mkdir .virtualenv

cd ~/code/cube-legacy-online/
mkvirtualenv cube-legacy-online
pip install -r requirements.txt
