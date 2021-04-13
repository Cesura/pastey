![logo](https://i.imgur.com/W22RFJZ.png)

A lightweight, self-hosted paste platform

# Features
* Self-contained system without external database dependencies
* Automatic programming language detection
* Optional on-disk encryption
* Optional single use pastes
* IP/network whitelisting and blocking
* Endpoint rate limiting
* Fully configurable via environment variables
* Included script for uploading files/content from stdin


## Screenshots
### Browser
![screenshot1](https://i.imgur.com/rQ5ZIg7.png)
![screenshot2](https://i.imgur.com/zaDpBaX.png)
![screenshot3](https://i.imgur.com/XDlJDZS.png)
### CLI
![screenshot4](https://i.imgur.com/FFWGe43.png)

# Installation
### Docker
It is highly recommended that you use the official Docker image to run Pastey. To do so, simply run:
```
$ docker run -d -p 5000:5000 -v /path/to/local/dir:/app/data cesura/pastey:latest
```
Change **/path/to/local/dir** to a local folder you would like to use for persistent paste storage. It will be mounted in the container at **/app/data**.

Pastey will then be accessable at *http://localhost:5000*

### Docker (non-AVX processor)
If your processor does not have support for AVX instructions, the "latest" image will fail to run. This is due to a decision by Tensorflow to enable this compile flag by default in version 1.5+. However, Anaconda's distribution of Tensorflow supports older architectures even in the 2.x line. You can instead use the image tagged ***latest-conda***:
```
$ docker run -d -p 5000:5000 -v /path/to/local/dir:/app/data cesura/pastey:latest-conda
```

### Local
Requirements:
* Python 3.8
* AVX-enabled processor (or a Python environment configured to use Anaconda's Tensorflow)

```
$ git clone https://github.com/Cesura/pastey.git && cd pastey
$ pip3 install -r requirements.txt
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
| PASTEY_RESTRICT_RAW_PASTING | restrict_raw_pasting | Enable/disable restricting of pasting via /raw to whitelisted users                                                                                                                              | True                                                                      |
| PASTEY_RATE_LIMIT           | rate_limit           | Rate limit for pasting, for non-whitelisted users                                                                                                                                                | 5/hour                                                                    |
| PASTEY_GUESS_THRESHOLD      | guess_threshold      | Threshold for automatic language detection guesses. If a result is below this value, it is treated as Plaintext.                                                                                 | 0.20                                                                      |
| PASTEY_RECENT_PASTES        | recent_pastes        | Number of recent pastes to show on the home page                                                                                                                                                 | 10                                                                        |
| PASTEY_BEHIND_PROXY         | behind_proxy         | Inform Pastey if it is behind a reverse proxy (nginx, etc.). If this is the case, it will rely on HTTP headers X-Real-IP or X-Forwarded-For. NOTE: Make sure your proxy config sets these values | False                                                                     |

### Docker configuration
For Docker environments, it is recommended that the options be passed to the container on startup: 
```
$ docker run -d -p 5000:5000 -e PASTEY_LISTEN_PORT=80 -e PASTEY_BEHIND_PROXY="True" cesura/pastey:latest
```
