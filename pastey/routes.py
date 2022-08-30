if __name__ == '__main__':
    from __main__ import app, limiter, loaded_config
else:
    from app import app, limiter, loaded_config
from . import config, common, functions

from flask import Flask, render_template, request, redirect, abort, make_response
from urllib.parse import quote
from datetime import datetime
from os import environ
import json
from base64 import b64decode

# Load themes
loaded_themes = common.get_themes()

# Load Languages
supported_languages = common.get_languages()

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
        script_url=common.build_url(request, "/pastey"))

# New paste page
@app.route("/new")
def new():
    whitelisted = common.verify_whitelist(common.get_source_ip(request))
    return render_template("new.html",
        whitelisted=whitelisted,
        languages=supported_languages,
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
        script_url=common.build_url(request, "/pastey"),
        whitelisted=whitelisted,
        active_theme=common.set_theme(request),
        themes=loaded_themes)

# View paste page
@app.route("/view/<unique_id>")
def view(unique_id):
    paste = functions.get_paste(unique_id)

    if paste is not None:
        return render_template("view.html",
            paste=paste,
            url=common.build_url(request, "/view/" + unique_id),
            whitelisted=common.verify_whitelist(common.get_source_ip(request)),
            active_theme=common.set_theme(request),
            themes=loaded_themes)
    else:
        abort(404)
        
# View paste page (raw)
@app.route("/view/<unique_id>/raw")
def view_raw(unique_id):
    paste = functions.get_paste(unique_id)

    if paste is not None:
        response = make_response(paste['content'], 200)
        response.mimetype = "text/plain"
        return response
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
    return render_template('pastey.sh', endpoint=common.build_url(request, "/paste")), 200, {
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

    # Content field is necessary
    if 'content' not in request.form:
        abort(400)

    content = request.form['content']

    # Check if content is empty
    if content.strip() == "":
        if 'cli' in request.form:
            abort(400)
        else:
            return redirect("/new")
    else:

        # Verify form options
        title = request.form['title'] if ('title' in request.form and request.form['title'].strip() != "") else "Untitled"
        single = True if 'single' in request.form else False
        encrypt = True if 'encrypt' in request.form else False
        expiration = int(request.form['expiration']) if 'expiration' in request.form else -1
        language = request.form['language'] if 'language' in request.form else "AUTO"

        # Create paste
        unique_id, key = functions.new_paste(title, content, source_ip, expires=expiration, single=single, encrypt=encrypt, language=language)
        if encrypt:

            # Return link if cli form option was set
            if 'cli' in request.form:
                return common.build_url(request, "/view/" + unique_id + "#" + quote(key)), 200
            else:
                return redirect("/view/" + unique_id + "#" + quote(key))
        else:
            if 'cli' in request.form:
                return common.build_url(request, "/view/" + unique_id), 200
            else:
                return redirect("/view/" + unique_id)

# POST new raw paste
@app.route('/raw', methods = ['POST'])
@limiter.limit(config.rate_limit, exempt_when=lambda: common.verify_whitelist(common.get_source_ip(request)))
def paste_raw():
    source_ip = common.get_source_ip(request)
    
    # Check if restrict pasting to whitelist CIDRs is enabled
    if config.restrict_pasting and not common.verify_whitelist(source_ip):
        abort(401)

    # Create paste
    unique_id, key = functions.new_paste("Untitled", request.data.decode('utf-8'), source_ip, single=False, encrypt=False)
    link = common.build_url(request, "/view/" + unique_id)

    return link, 200

# POST new json paste
@app.route('/json', methods = ['POST'])
@limiter.limit(config.rate_limit, exempt_when=lambda: common.verify_whitelist(common.get_source_ip(request)))
def paste_json():
    source_ip = common.get_source_ip(request)
    
    # Check if restrict pasting to whitelist CIDRs is enabled
    if config.restrict_pasting and not common.verify_whitelist(source_ip):
        abort(401)

    # Check json integrity
    try:
        paste = json.loads(request.data)
    except json.JSONDecodeError:
        abort(400)
    
    # Content field is mandatory
    if 'content' not in paste or paste['content'].strip() == "":
        abort(400)
    content = paste['content']

    # Check if content was base64 encoded (from the CLI client typically)
    from_client = False
    if 'base64' in paste and paste['base64'] == True:
      from_client = True
      content = b64decode(content).decode("utf-8")

    # Optional fields
    title = paste['title'] if ('title' in paste and paste['title'].strip() != "") else "Untitled"
    single = paste['single'] if ('single' in paste and type(paste['single']) == bool) else False
    encrypt = paste['encrypt'] if ('encrypt' in paste and type(paste['encrypt']) == bool) else False
    expiration = paste['expiration'] if ('expiration' in paste and type(paste['expiration']) == int) else -1
    language = paste['language'] if ('language' in paste and type(paste['language']) == str) else "AUTO"

    # Create paste
    unique_id, key = functions.new_paste(title, content, source_ip, expires=expiration, single=single, encrypt=encrypt, language=language)
    if encrypt:
        if from_client:
          return common.build_url(request, "/view/" + unique_id + "#" + quote(key)), 200
        else:
          return {
              "link": common.build_url(request, "/view/" + unique_id + "#" + quote(key))
          }, 200
    else:
        if from_client:
          return common.build_url(request, "/view/" + unique_id), 200
        else:
          return {
              "link": common.build_url(request, "/view/" + unique_id)
          }, 200

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
