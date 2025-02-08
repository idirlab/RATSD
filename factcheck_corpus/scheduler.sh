#!/bin/bash
if [ -z "$1" ]; then
    python3 ./politifact/politifact_main.py >> ./log.txt
    python3 ./snopes/snopes_main.py >> ./log.txt
    python3 ./metafact/metafact_main.py >> ./log.txt
    python3 ./fullfact/fullfact_main.py >> ./log.txt
    python3 ./factcheckafp/factcheckafp_main.py >> ./log.txt
    python3 ./factcheckorg/factcheckorg_main.py >> ./log.txt
    python3 ./apnews/apnews_main.py >> ./log.txt
    python3 ./utils/email_notifier.py
else
    cd /factcheckrepo
    python3 ./politifact/politifact_main.py >> ./log.txt
    python3 ./snopes/snopes_main.py >> ./log.txt
    python3 ./metafact/metafact_main.py >> ./log.txt
    python3 ./fullfact/fullfact_main.py >> ./log.txt
    python3 ./factcheckafp/factcheckafp_main.py >> ./log.txt
    python3 ./factcheckorg/factcheckorg_main.py >> ./log.txt
    python3 ./apnews/apnews_main.py >> ./log.txt
    python3 ./utils/email_notifier.py
fi