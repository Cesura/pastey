from __main__ import app, limiter, loaded_config
from . import config, common, functions

from flask import Flask, render_template, request, redirect, abort
from urllib.parse import quote
from datetime import datetime
from os import environ

# Load themes
loaded_themes = common.get_themes()

# Set rate limit
# Workaround for @limiter annotations being parsed early
config.rate_limit = environ["PASTEY_RATE_LIMIT"] if "PASTEY_RATE_LIMIT" in environ else config.rate_limit

########## Routes ##########

# Home page
@app.route("/")
def home():
    whitelisted = common.verify_whitelist(common.get_source_ip(request))
    pastes = []

    if whitelisted or config.force_show_recent:
        pastes = functions.get_recent()

    return render_template("index.html",
        pastes=pastes,
        whitelisted=whitelisted, 
        active_theme=common.set_theme(request),
        themes=loaded_themes,
        force_show_recent=config.force_show_recent,
        show_cli_button=config.show_cli_button,
        script_url=request.url.rsplit('/', 1)[0] + "/pastey")

# New paste page
@app.route("/new")
def new():
    whitelisted = common.verify_whitelist(common.get_source_ip(request))
    return render_template("new.html",
        whitelisted=whitelisted,
        active_theme=common.set_theme(request),
        themes=loaded_themes)

# Config page
@app.route("/config")
def config_page():
    whitelisted = common.verify_whitelist(common.get_source_ip(request))
    if not whitelisted:
        abort(401)

    return render_template("config.html",
        config_items=loaded_config, 
        script_url=request.url.rsplit('/', 1)[0] + "/pastey",
        whitelisted=whitelisted,
        active_theme=common.set_theme(request),
        themes=loaded_themes)

# View paste page
@app.route("/view/<unique_id>")
def view(unique_id):
    content = functions.get_paste(unique_id)

    if content is not None:
        return render_template("view.html",
            paste=content,
            url=request.url,
            whitelisted=common.verify_whitelist(common.get_source_ip(request)),
            active_theme=common.set_theme(request),
            themes=loaded_themes)
    else:
        abort(404)

# View paste page (encrypted)
@app.route("/view/<unique_id>/<key>")
def view_key(unique_id, key):
    content = functions.get_paste(unique_id, key=key)

    if content == 401:
        abort(401)
    elif content is not None:
        return render_template("view.html",
            paste=content,
            url=request.url,
            whitelisted=common.verify_whitelist(common.get_source_ip(request)),
            active_theme=common.set_theme(request),
            themes=loaded_themes)
    else:
        abort(404)


# Delete paste
@app.route("/delete/<unique_id>")
def delete(unique_id):
    if not common.verify_whitelist(common.get_source_ip(request)):
        abort(401)

    functions.delete_paste(unique_id)
    return redirect("/")

# Script download
@app.route("/pastey")
def pastey_script():
    return render_template('pastey.sh', endpoint=request.url.rsplit('/', 1)[0] + "/raw"), 200, {
        'Content-Disposition': 'attachment; filename="pastey"',
        'Content-Type': 'text/plain'
    }

# POST new paste
@app.route('/paste', methods = ['POST'])
@limiter.limit(config.rate_limit, exempt_when=lambda: common.verify_whitelist(common.get_source_ip(request)))
def paste():
    source_ip = common.get_source_ip(request)

    # Check if restrict pasting to whitelist CIDRs is enabled
    if config.restrict_pasting and not common.verify_whitelist(source_ip):
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
        unique_id, key = functions.new_paste(title, content, source_ip, expires=int(request.form['expiration']), single=single, encrypt=encrypt)
        if encrypt:
            return redirect("/view/" + unique_id + "/" + quote(key))
        else:
            return redirect("/view/" + unique_id)

# POST new raw paste
@app.route('/raw', methods = ['POST'])
@limiter.limit(config.rate_limit, exempt_when=lambda: common.verify_whitelist(common.get_source_ip(request)))
def raw():
    source_ip = common.get_source_ip(request)
    
    # Check if restrict pasting to whitelist CIDRs is enabled
    if config.restrict_raw_pasting and not common.verify_whitelist(source_ip):
        abort(401)

    # Create paste
    unique_id, key = functions.new_paste("Untitled", request.data.decode('utf-8'), source_ip, single=False, encrypt=False)
    link = request.url.rsplit('/', 1)[0] + "/view/" + unique_id

    return link, 200

# Custom 404 handler
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html',
        whitelisted=common.verify_whitelist(common.get_source_ip(request)),
        active_theme=common.set_theme(request),
        themes=loaded_themes), 404

# Custom 401 handler
@app.errorhandler(401)
def unauthorized(e):
    return render_template('401.html',
        whitelisted=common.verify_whitelist(common.get_source_ip(request)),
        active_theme=common.set_theme(request),
        themes=loaded_themes), 401
