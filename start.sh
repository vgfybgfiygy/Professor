if [ -z $UPSTREAM_REPO ]
then
  echo "Cloning main Repository"
  git clone https://github.com/Hansaka-Anuhas/SL-Auto-Filter-Bot.git /SL-Auto-Filter-Bot
else
  echo "Cloning Custom Repo from $UPSTREAM_REPO "
  git clone $UPSTREAM_REPO /SL-Auto-Filter-Bot
fi
cd /SL-Auto-Filter-Bot
pip3 install -U -r requirements.txt
echo "Starting Bot..."
python3 bot.py
