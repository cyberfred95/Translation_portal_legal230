cd /home/ubuntu/legal230-latest && . ../.bashrc_lexamt.sh
cd /home/ubuntu/legal230-latest && python3 -m django makemessages -l fr -l en --ignore=static_collected/* --ignore=static/* --ignore=node_modules/* | cat
cd /home/ubuntu/legal230-latest && python3 -m django compilemessages -l fr -l en | cat
