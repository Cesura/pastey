from flask import Flask, render_template, request, redirect, abort
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from guesslang import Guess
from os import environ
from distutils.util import strtobool
from threading import Thread

pastey_version = "0.5"
loaded_config = {}
loaded_themes = []

app = Flask(__name__)
limiter = Limiter(
    app,
    key_func=get_remote_address
)
guess = Guess()

from pastey import config, common, routes, functions

# Check environment variable overrides
config.data_directory = environ["PASTEY_DATA_DIRECTORY"] if "PASTEY_DATA_DIRECTORY" in environ else config.data_directory
config.listen_address = environ["PASTEY_LISTEN_ADDRESS"] if "PASTEY_LISTEN_ADDRESS" in environ else config.listen_address
config.listen_port = environ["PASTEY_LISTEN_PORT"] if "PASTEY_LISTEN_PORT" in environ else config.listen_port
config.use_whitelist = bool(strtobool(environ["PASTEY_USE_WHITELIST"])) if "PASTEY_USE_WHITELIST" in environ else config.use_whitelist
config.restrict_pasting = bool(strtobool(environ["PASTEY_RESTRICT_PASTING"])) if "PASTEY_RESTRICT_PASTING" in environ else config.restrict_pasting
config.guess_threshold = float(environ["PASTEY_GUESS_THRESHOLD"]) if "PASTEY_GUESS_THRESHOLD" in environ else config.guess_threshold
config.recent_pastes = int(environ["PASTEY_RECENT_PASTES"]) if "PASTEY_RECENT_PASTES" in environ else config.recent_pastes
config.whitelist_cidr = environ["PASTEY_WHITELIST_CIDR"].split(",") if "PASTEY_WHITELIST_CIDR" in environ else config.whitelist_cidr
config.blacklist_cidr = environ["PASTEY_BLACKLIST_CIDR"].split(",") if "PASTEY_BLACKLIST_CIDR" in environ else config.blacklist_cidr
config.behind_proxy = bool(strtobool(environ["PASTEY_BEHIND_PROXY"])) if "PASTEY_BEHIND_PROXY" in environ else config.behind_proxy
config.default_theme = environ["PASTEY_DEFAULT_THEME"] if "PASTEY_DEFAULT_THEME" in environ else config.default_theme
config.purge_interval = int(environ["PASTEY_PURGE_INTERVAL"]) if "PASTEY_PURGE_INTERVAL" in environ else config.purge_interval
config.force_show_recent = bool(strtobool(environ["PASTEY_FORCE_SHOW_RECENT"])) if "PASTEY_FORCE_SHOW_RECENT" in environ else config.force_show_recent
config.ignore_guess = environ["PASTEY_IGNORE_GUESS"].split(",") if "PASTEY_IGNORE_GUESS" in environ else config.ignore_guess
config.show_cli_button = bool(strtobool(environ["PASTEY_SHOW_CLI_BUTTON"])) if "PASTEY_SHOW_CLI_BUTTON" in environ else config.show_cli_button
config.force_https_links = bool(strtobool(environ["PASTEY_FORCE_HTTPS_LINKS"])) if "PASTEY_FORCE_HTTPS_LINKS" in environ else config.force_https_links
config.override_domain = environ["PASTEY_OVERRIDE_DOMAIN"] if "PASTEY_OVERRIDE_DOMAIN" in environ else config.override_domain

loaded_config['pastey_version'] = pastey_version
app.logger.info("Pastey version %s", pastey_version)
app.logger.info("USING THE FOLLOWING CONFIGURATION:")
for option in dir(config):
    if not option.startswith("__"):
        loaded_config[option] = eval("config.%s" % option)
        app.logger.info("%s: %s", option, loaded_config[option])

# Register error handlers
app.register_error_handler(404, routes.page_not_found)
app.register_error_handler(401, routes.unauthorized)

# Start purging expired pastes thread
purge_thread = Thread(target=functions.purge_expired_pastes, daemon=True)
purge_thread.start()

# Main loop
if __name__ == "__main__":
    app.run(host=config.listen_address, port=config.listen_port)
