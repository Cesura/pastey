from __main__ import app
from __main__ import guess    # Intentionally put on a separate line

from . import config, common

from os import path, remove, listdir
from pathlib import Path
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
import time
import secrets
import math
import json
from os import environ

########## Paste functions ##########

config.recent_pastes = int(environ["PASTEY_RECENT_PASTES"]) if "PASTEY_RECENT_PASTES" in environ else config.recent_pastes

# Get recent n pastes, defined in config by recent_pastes
def get_recent(limit=config.recent_pastes):
    paths = sorted(Path(config.data_directory).iterdir(), key=path.getmtime, reverse=True)

    recent_pastes = []
    i = 0
    while i < limit and i < len(paths):
        if paths[i].is_file():
            with open(paths[i]) as fp:
                try:
                    paste = json.loads(fp.read())
                except json.JSONDecodeError:
                    i += 1
                    continue

                # Set extra metadata
                basename = path.basename(paths[i])
                paste['unique_id'] = basename[:-8] if basename.endswith(".expires") else basename
                paste['content'] = '\n'.join(paste['content'].splitlines()[0:10])
                paste['icon'] = common.get_icon(paste['language'])

                # Replace preview if encrypted
                if paste['encrypted']:
                    paste['content'] = "[Encrypted]"
                    paste['title'] = "[Encrypted]"

                recent_pastes.append(paste)
        i += 1

    return recent_pastes

# Get paste by ID
def get_paste(unique_id, key=""):
    file_path = common.determine_file(unique_id)

    if file_path is not None:
        with open(file_path, "r") as fp:
            try:
                paste = json.loads(fp.read())
            except json.JSONDecodeError:
                return None

        # Check if paste is expired
        if common.is_expired(paste):
            delete_paste(unique_id)
            return None

        # Check remaining uses, and decrement
        # -1 = unlimited uses
        if paste['uses'] != -1:
            paste['uses'] -= 1
            if paste['uses'] == 0:
                delete_paste(unique_id)
            else:
                with open(file_path, "w") as fp:
                    fp.write(json.dumps(paste))

        return paste
    else:
        return None

# Delete paste by ID
def delete_paste(unique_id):
    paste = common.determine_file(unique_id)
    if paste is not None:
        remove(paste)

# Create new paste
def new_paste(title, content, source_ip, expires=0, single=False, encrypt=False, language="AUTO"):
    # this calculates the number of digits of a base64 number needed to be unlikely to have collisions
    id_len = int(math.ceil( 3*math.log(len(listdir(config.data_directory))+1)/math.log(256) + 1.5 ))
    unique_id = secrets.token_urlsafe(id_len if id_len >= config.minimum_url_length else config.minimum_url_length)
    output_file = config.data_directory + "/" + unique_id

    # Check for existing paste id (unlikely)
    while path.exists(output_file) or path.exists(output_file + ".expires"):
        unique_id = secrets.token_urlsafe(id_len if id_len >= config.minimum_url_length else config.minimum_url_length)
        output_file = config.data_directory + "/" + unique_id

    # Attempt to guess programming language
    if language == "AUTO":
        guesses = guess.probabilities(content)
        language = guesses[0][0] if guesses[0][1] > config.guess_threshold and guesses[0][0] not in config.ignore_guess else "Plaintext"

    # Check if encryption is necessary
    key = ""
    if encrypt:
        init_key = Fernet.generate_key()
        cipher_suite = Fernet(init_key)

        # Encrypt title and content
        content = cipher_suite.encrypt(content.encode('utf-8')).decode('utf-8')
        title = cipher_suite.encrypt(title.encode('utf-8')).decode('utf-8')
        key = init_key.decode('utf-8')

    # Check if single use is set
    uses = 2 if single else -1

    # Check for expiration
    now = datetime.now()
    expiration = ""
    if expires > 0:
        expiration = (now + timedelta(hours=expires)).strftime("%a, %d %b %Y at %H:%M:%S")
        output_file = output_file + ".expires"

    output = {
        "timestamp": now.strftime("%a, %d %b %Y at %H:%M:%S"),
        "language": language,
        "source_ip": source_ip,
        "title": title,
        "content": content,
        "encrypted": encrypt,
        "uses": uses,
        "expiration": expiration
    }

    # Write to output file
    with open(output_file, "w+") as fp:
        fp.write(json.dumps(output))

    return unique_id, key

# Purge expired pastes
def purge_expired_pastes():
    print("Starting purge thread, with interval {0} seconds...".format(config.purge_interval))
    while True:
        for paste in Path(config.data_directory).iterdir():
            if str(paste).endswith(".expires"):
                unique_id = path.basename(paste)[:-8]

                with open(paste, "r") as fp:
                    content = json.loads(fp.read())
                    
                    # Check if paste is expired
                    if common.is_expired(content):
                        delete_paste(unique_id)
        
        # Sleep for specified interval
        time.sleep(config.purge_interval)
