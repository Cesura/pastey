![logo](https://i.imgur.com/W22RFJZ.png)

A minimal, self-hosted paste platform

# Features
* Self-contained system without external database dependencies
* Automatic programming language detection
* Optional on-disk encryption
* Optional single use pastes
* Optional expiration date
* QR code generation
* Theme system
* IP/network whitelisting and blocking
* Endpoint rate limiting
* JSON API
* Fully configurable via environment variables
* Included script for uploading files/content from stdin


## Screenshots
### Browser
![home](https://i.imgur.com/P3BSv9d.png)
![new](https://i.imgur.com/5YiQ3GB.png)
![view](https://i.imgur.com/4bkPKNP.png)
### Dark
![dark](https://i.imgur.com/SXeSa5d.png)
### CLI
![screenshot5](https://i.imgur.com/kV7q1Zv.png)

# Installation
### Docker
It is highly recommended that you use the official Docker image to run Pastey. To do so, simply run:
```
$ docker run -d -p 5000:5000 -v /path/to/local/dir:/app/data cesura/pastey:latest
```
Change **/path/to/local/dir** to a local folder you would like to use for persistent paste storage. It will be mounted in the container at **/app/data**.

Pastey will then be accessible at *http://localhost:5000*

### Docker (slim image OR non-AVX processor)
If you're interested in a slimmer image (or your processor does not have support for AVX instructions required by Tensorflow), a slim image without language detection is also maintained:
```
$ docker run -d -p 5000:5000 -v /path/to/local/dir:/app/data cesura/pastey:latest-slim
```

### docker-compose
If you prefer to use docker-compose:
```
$ wget https://raw.githubusercontent.com/Cesura/pastey/main/docker-compose.yml && docker-compose up -d
```
Note that this must be modified if you wish to use a local directory for storage, rather than a Docker volume.

### Local
#### With language detection
Requirements:
* Python 3.8
* AVX-enabled processor (or a Python environment configured to use Anaconda's Tensorflow)

```
$ git clone https://github.com/Cesura/pastey.git && cd pastey && mkdir ./data
$ pip3 install -r requirements.txt
$ python3 app.py 
```

#### Without language detection
If you prefer to not use the language detection feature, use the included **patch_no_tensorflow.sh** script to remove the guesslang requirements:
```
$ git clone https://github.com/Cesura/pastey.git && cd pastey && mkdir ./data
$ ./patch_no_tensorflow.sh && pip3 install -r requirements.txt
$ python3 app.py 
```

# Configuration
Here is a list of the available configuration options:
| Environment Variable        | config.py Variable   | Description                                                                                                                                                                                      | Default Value                                                             |
|-----------------------------|----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------------|
| PASTEY_DATA_DIRECTORY       | data_directory       | Local directory for paste storage                                                                                                                                                                | ./data                                                                    |
| PASTEY_LISTEN_ADDRESS       | listen_address       | Address to listen on                                                                                                                                                                             | 0.0.0.0                                                                   |
| PASTEY_LISTEN_PORT          | listen_port          | Port to listen on                                                                                                                                                                                | 5000                                                                      |
| PASTEY_USE_WHITELIST        | use_whitelist        | Enable/disable whitelisting for admin tasks (view recent, delete, config)                                                                                                                        | True                                                                      |
| PASTEY_WHITELIST_CIDR       | whitelist_cidr       | List of whitelisted IP addresses or networks (in CIDR format). When passed as an environment variable, it should be a comma-separated list.                                                      | [ '127.0.0.1/32' ,  '10.0.0.0/8' ,  '172.16.0.0/12' ,  '192.168.0.0/16' ] |
| PASTEY_BLACKLIST_CIDR       | blacklist_cidr       | List of blocked IP addresses or networks (in CIDR format). When passed as an environment variable, it should be a comma-separated list.                                                          | []                                                                        |
| PASTEY_RESTRICT_PASTING     | restrict_pasting     | Enable/disable restricting of pasting to whitelisted users                                                                                                                                       | False                                                                     |
| PASTEY_RATE_LIMIT           | rate_limit           | Rate limit for pasting, for non-whitelisted users                                                                                                                                                | 5/hour                                                                    |
| PASTEY_GUESS_THRESHOLD      | guess_threshold      | Threshold for automatic language detection guesses. If a result is below this value, it is treated as Plaintext.                                                                                 | 0.20                                                                      |
| PASTEY_RECENT_PASTES        | recent_pastes        | Number of recent pastes to show on the home page                                                                                                                                                 | 10                                                                        |
| PASTEY_BEHIND_PROXY         | behind_proxy         | Inform Pastey if it is behind a reverse proxy (nginx, etc.). If this is the case, it will rely on HTTP headers X-Real-IP or X-Forwarded-For. NOTE: Make sure your proxy config sets these values | False                                                                     |
| PASTEY_DEFAULT_THEME        | default_theme        | Select which theme Pastey should use by default. This is overridden by client options.                                                                                                           | Light                                                                     |
| PASTEY_PURGE_INTERVAL       | purge_interval       | Purge interval (in seconds) for checking expired pastes in background thread                                                                                                                     | 3600                                                                      |
| PASTEY_FORCE_SHOW_RECENT    | force_show_recent    | Show recent pastes on the home page, even to non-whitelisted users (without delete button)                                                                                                       | False                                                                     |
| PASTEY_IGNORE_GUESS         | ignore_guess         | Ignore these classifications for language detection                                                                                                                                              | ['TeX', 'SQL']                                                            |
| PASTEY_SHOW_CLI_BUTTON      | show_cli_button      | Enable/disabling showing of CLI button on home page                                                                                                                                              | True                                                                      |

### Docker configuration
For Docker environments, it is recommended that the options be passed to the container on startup: 
```
$ docker run -d -p 5000:5000 -e PASTEY_LISTEN_PORT=80 -e PASTEY_BEHIND_PROXY="True" cesura/pastey:latest
```
