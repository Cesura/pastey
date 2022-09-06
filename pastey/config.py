# Data directory
data_directory = "./data"

# Listen address
listen_address = "0.0.0.0"

# Listen port
listen_port = 5000

# Use whitelisting
# Whitelisted IPs can view recent pastes on the home page, as well as delete pastes
# For limiting pasting to whitelisted users, enable the "restrict_pasting" option below
use_whitelist = True

# Whitelist CIDR
whitelist_cidr = ['127.0.0.1/32', '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16']

# Blacklist CIDR
blacklist_cidr = []

# Restrict pasting functionality to whitelisted IPs
restrict_pasting = False

# Rate limit for pasting (ignored for whitelisted users)
rate_limit = "5/hour"

# Guess threshold for automatic language detection
guess_threshold = 0.20

# Number of recent pastes to show on the home page
recent_pastes = 10

# Try to use X-Real-IP or X-Forwarded-For HTTP headers
behind_proxy = False

# Default theme to display to users
default_theme = "Light"

# Purge interval (in seconds) for checking expired pastes
purge_interval = 3600

# Show recent pastes, even to non-whitelisted users (without a delete button)
force_show_recent = False

# Ignore these classifications for language detection
ignore_guess = ['TeX', 'SQL']

# Show CLI button on home page
show_cli_button = True

# Include https in the generated links instead of http
# This assumes you are behind something else doing the SSL
# termination, but want the users to see https links
#
# This is normally handled by the HTTP headers now
force_https_links = False

# This can be used to specify a different domain for generated links
#
# Note: exclude the http:// or https:// prefix, as well as anything 
# following the domain (except the port, if applicable)
override_domain = ""

# Minumum number of characters for generated URLs
minimum_url_length = 5
