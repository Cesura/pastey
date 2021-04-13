from flask import Flask, render_template, request, redirect, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from guesslang import Guess
from datetime import datetime
from urllib.parse import quote
from cryptography.fernet import Fernet
import ipaddress
import uuid
import json
from os import path, remove, environ
from pathlib import Path
from config import config
from distutils.util import strtobool

app = Flask(__name__)
limiter = Limiter(
    app,
    key_func=get_remote_address
)
guess = Guess()

# Pastey version
pastey_version = "0.2"
loaded_config = {}

# Check environment variable overrides
config.data_directory = environ["PASTEY_DATA_DIRECTORY"] if "PASTEY_DATA_DIRECTORY" in environ else config.data_directory
config.listen_address = environ["PASTEY_LISTEN_ADDRESS"] if "PASTEY_LISTEN_ADDRESS" in environ else config.listen_address
config.listen_port = environ["PASTEY_LISTEN_PORT"] if "PASTEY_LISTEN_PORT" in environ else config.listen_port
config.use_whitelist = bool(strtobool(environ["PASTEY_USE_WHITELIST"])) if "PASTEY_USE_WHITELIST" in environ else config.use_whitelist
config.restrict_pasting = bool(strtobool(environ["PASTEY_RESTRICT_PASTING"])) if "PASTEY_RESTRICT_PASTING" in environ else config.restrict_pasting
config.restrict_raw_pasting = bool(strtobool(environ["PASTEY_RESTRICT_RAW_PASTING"])) if "PASTEY_RESTRICT_RAW_PASTING" in environ else config.restrict_raw_pasting
config.rate_limit = environ["PASTEY_RATE_LIMIT"] if "PASTEY_RATE_LIMIT" in environ else config.rate_limit
config.guess_threshold = float(environ["PASTEY_GUESS_THRESHOLD"]) if "PASTEY_GUESS_THRESHOLD" in environ else config.guess_threshold
config.recent_pastes = int(environ["PASTEY_RECENT_PASTES"]) if "PASTEY_RECENT_PASTES" in environ else config.recent_pastes
config.whitelist_cidr = environ["PASTEY_WHITELIST_CIDR"].split(",") if "PASTEY_WHITELIST_CIDR" in environ else config.whitelist_cidr
config.blacklist_cidr = environ["PASTEY_BLACKLIST_CIDR"].split(",") if "PASTEY_BLACKLIST_CIDR" in environ else config.blacklist_cidr
config.behind_proxy = bool(strtobool(environ["PASTEY_BEHIND_PROXY"])) if "PASTEY_BEHIND_PROXY" in environ else config.behind_proxy

# Check request IP is in config whitelist
def verify_whitelist(ip):
    address = ipaddress.ip_address(ip)

    # Check blacklist
    for network in config.blacklist_cidr:
        if address in ipaddress.IPv4Network(network):
            return False

    if not config.use_whitelist:
        return True

    # Check whitelist
    for network in config.whitelist_cidr:
        if address in ipaddress.IPv4Network(network):
            return True
    
    return False

# Solve anomalies in icon naming
def get_icon(language):
    if language == "C#":
        return "csharp"
    elif language == "C++":
        return "cplusplus"
    elif language == "Jupyter Notebook":
        return "jupyter"
    else:
        return language.lower()

# For handling reverse proxy configurations
# Note that these are HTTP headers and are generally untrustworthy
# Make sure your proxy configuration is either setting or clearing these
def get_source_ip(request):
    if config.behind_proxy:
        if 'X-Real-IP' in request.headers:
            return request.headers['X-Real-IP']
        elif 'X-Forwarded-For' in request.headers:
            return request.headers['X-Forwarded-For']

    return request.remote_addr

########## Paste functions ##########

# Get recent n pastes, defined in config by recent_pastes
def get_recent(limit=config.recent_pastes):
    paths = sorted(Path(config.data_directory).iterdir(), key=path.getmtime, reverse=True)

    recent_pastes = []
    i = 0
    while i < limit and i < len(paths):
        with open(paths[i]) as fp:
            paste = json.loads(fp.read())
            paste['unique_id'] = path.basename(paths[i])
            paste['content'] = '\n'.join(paste['content'].splitlines()[0:10])
            paste['icon'] = get_icon(paste['language'])

            if paste['encrypted']:
                paste['content'] = "[Encrypted]"

            recent_pastes.append(paste)
        i += 1

    return recent_pastes

# Get paste by ID
def get_paste(unique_id, key=""):
    if path.exists(config.data_directory + "/" + unique_id):
        with open(config.data_directory + "/" + unique_id, "r") as fp:
            paste = json.loads(fp.read())

        # Check remaining uses, and decrement
        # -1 = unlimited uses
        if paste['uses'] != -1:
            paste['uses'] -= 1
            if paste['uses'] == 0:
                delete_paste(unique_id)
            else:
                with open(config.data_directory + "/" + unique_id, "w") as fp:
                    fp.write(json.dumps(paste))

        # Decrypt content, if necessary
        try:
            if key != "":
                cipher_suite = Fernet(key.encode('utf-8'))
                paste['content'] = cipher_suite.decrypt(paste['content'].encode('utf-8')).decode('utf-8')
        except Exception as e:
            return 401

        return paste
    else:
        return None

# Delete paste by ID
def delete_paste(unique_id):
    paste = config.data_directory + "/" + unique_id
    if path.exists(paste):
        remove(paste)

# Create new paste
def new_paste(title, content, source_ip, single=False, encrypt=False):
    unique_id = str(uuid.uuid4())
    while path.exists(config.data_directory + "/" + unique_id):
        unique_id = str(uuid.uuid4())

    # Attempt to guess programming language
    guesses = guess.probabilities(content)
    language = guesses[0][0] if guesses[0][1] > config.guess_threshold and guesses[0][0] != "SQL" else "Plaintext"

    # Check if encryption is necessary
    key = ""
    if encrypt:
        init_key = Fernet.generate_key()
        cipher_suite = Fernet(init_key)
        content = cipher_suite.encrypt(content.encode('utf-8')).decode('utf-8')
        key = init_key.decode('utf-8')

    # Check if single use is set
    uses = 2 if single else -1

    output = {
        "timestamp": datetime.now().strftime("%a, %d %b %Y at %H:%M:%S"),
        "language": language,
        "source_ip": source_ip,
        "title": title,
        "content": content,
        "encrypted": encrypt,
        "uses": uses
    }

    # Write to output file
    with open(config.data_directory + "/" + unique_id, "w+") as fp:
        fp.write(json.dumps(output))

    return unique_id, key

########## Routes ##########

# Home page
@app.route("/")
def home():
    whitelisted = verify_whitelist(get_source_ip(request))
    pastes = []

    if whitelisted:
        pastes=get_recent()

    return render_template("index.html", pastes=pastes, whitelisted=whitelisted)

# New paste page
@app.route("/new")
def new():
    whitelisted = verify_whitelist(get_source_ip(request))
    return render_template("new.html", whitelisted=whitelisted)

# Config page
@app.route("/config")
def config_page():
    whitelisted = verify_whitelist(get_source_ip(request))
    if not whitelisted:
        abort(401)

    return render_template("config.html", config_items=loaded_config, 
        script_url=request.url.rsplit('/', 1)[0] + "/pastey", whitelisted=whitelisted)

# View paste page
@app.route("/view/<unique_id>")
def view(unique_id):
    whitelisted = verify_whitelist(get_source_ip(request))

    content = get_paste(unique_id)
    if content is not None:
        return render_template("view.html", paste=content, url=request.url, whitelisted=whitelisted)
    else:
        abort(404)

# View paste page (encrypted)
@app.route("/view/<unique_id>/<key>")
def view_key(unique_id, key):
    whitelisted = verify_whitelist(get_source_ip(request))
    content = get_paste(unique_id, key=key)

    if content == 401:
        abort(401)
    elif content is not None:
        return render_template("view.html", paste=content, url=request.url, whitelisted=whitelisted)
    else:
        abort(404)


# Delete paste
@app.route("/delete/<unique_id>")
def delete(unique_id):
    if not verify_whitelist(get_source_ip(request)):
        abort(401)

    delete_paste(unique_id)
    return redirect("/")

@app.route("/pastey")
def pastey_script():
    return render_template('pastey.sh', endpoint=request.url.rsplit('/', 1)[0] + "/raw"), 200, {
        'Content-Disposition': 'attachment; filename="pastey"',
        'Content-Type': 'text/plain'
    }

# POST new paste
@app.route('/paste', methods = ['POST'])
@limiter.limit(config.rate_limit, exempt_when=lambda: verify_whitelist(get_source_ip(request)))
def paste():
    source_ip = get_source_ip(request)

    # Check if restrict pasting to whitelist CIDRs is enabled
    if config.restrict_pasting and not verify_whitelist(source_ip):
        abort(401)

    content = request.form['content']

    # Check if content is empty
    if request.form['content'].strip() == "":
        return redirect("/new")
    else:

        # Verify form options
        title = request.form['title'] if request.form['title'].strip() != "" else "Untitled"
        single = True if 'single' in request.form else False
        encrypt = True if 'encrypt' in request.form else False
        
        # Create paste
        unique_id, key = new_paste(title, content, source_ip, single=single, encrypt=encrypt)
        if encrypt:
            return redirect("/view/" + unique_id + "/" + quote(key))
        else:
            return redirect("/view/" + unique_id)

# POST new raw paste
@app.route('/raw', methods = ['POST'])
@limiter.limit(config.rate_limit, exempt_when=lambda: verify_whitelist(get_source_ip(request)))
def raw():
    source_ip = get_source_ip(request)
    
    # Check if restrict pasting to whitelist CIDRs is enabled
    if config.restrict_raw_pasting and not verify_whitelist(source_ip):
        abort(401)

    # Create paste
    unique_id, key = new_paste("Untitled", request.data.decode('utf-8'), source_ip, single=False, encrypt=False)
    link = request.url.rsplit('/', 1)[0] + "/view/" + unique_id

    return link, 200


# Custom 404 handler
@app.errorhandler(404)
def page_not_found(e):
    whitelisted = verify_whitelist(get_source_ip(request))
    return render_template('404.html', whitelisted=whitelisted), 404

# Custom 401 handler
@app.errorhandler(401)
def unauthorized(e):
    whitelisted = verify_whitelist(get_source_ip(request))
    return render_template('401.html', whitelisted=whitelisted), 401

# Main loop
if __name__ == "__main__":
    
    # Print configuration
    print("=====================================")
    print("Pastey version ", pastey_version)
    print("USING THE FOLLOWING CONFIGURATION:")
    print("=====================================")
    for option in dir(config):
        if not option.startswith("__"):
            loaded_config[option] = eval("config.%s" % option)
            print(option, ": ", loaded_config[option])
    print("=====================================")

    # Register error handlers
    app.register_error_handler(404, page_not_found)
    app.register_error_handler(401, unauthorized)

    app.run(host=config.listen_address, port=config.listen_port)