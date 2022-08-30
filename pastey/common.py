from . import config
if __name__ == '__main__':
    from __main__ import guess
else:
    from app import guess
import ipaddress
from os import path
from pathlib import Path
from datetime import datetime, timedelta

########## Common functions ##########

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
    elif language == "Visual Basic":
        return "vb"
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

# Determine theme by checking for cookie, or returning default
def set_theme(request):
    if 'pastey_theme' in request.cookies:
        return request.cookies['pastey_theme']
    return config.default_theme

# Get a sorted list of all themes in the theme dir
def get_themes():
    themes = []
    for path in Path("./static/themes/").iterdir():
        themes.append(str(path).split('/')[-1].split('.')[0])
    return sorted(themes, key=str.casefold)

# Get a list of all supported languages from guesslang
def get_languages():
    return guess.supported_languages

# Get file path from unique id
# This is a wrapper to check for files with the .expires extension
def determine_file(unique_id):
    attempt = config.data_directory + "/" + unique_id
    if path.exists(attempt):
        return attempt
    
    # Check for expiration format
    attempt = attempt + ".expires"
    if path.exists(attempt):
        return attempt

    return None

# Take a paste object and check if it is expired
def is_expired(paste):
    if 'expiration' in paste and paste['expiration'] != "":
        expires = datetime.strptime(paste['expiration'], "%a, %d %b %Y at %H:%M:%S")

        if expires < datetime.now():
            return True
    
    return False

# Build a URL, accounting for config options
def build_url(request, path="/"):
    domain = request.url.split('//')[1].split("/")[0] if config.override_domain == "" else config.override_domain

    # Check for HTTPS headers
    if 'X-Forwarded-Proto' in request.headers and request.headers['X-Forwarded-Proto'] == "https":
        protocol = "https:"
    elif 'X-Forwarded-Port' in request.headers and request.headers['X-Forwarded-Port'] == "443":
        protocol = "https:"
    else:
        protocol = request.url.split('//')[0] if not config.force_https_links else "https:"

    return protocol + "//" + domain + path
