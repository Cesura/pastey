#!/bin/bash

# Patch functions.py
sed -i '/^[^#]/ s/\(^.*guesses = guess.probabilities.*$\)/#\ \1/' pastey/functions.py
sed -i '/^[^#]/ s/\(^.*from __main__ import guess.*$\)/#\ \1/' pastey/functions.py
sed -i '/^[^#]/ s/\(^.*language = guesses.*$\)/        language = "Plaintext"/' pastey/functions.py

# Patch app.py
sed -i '/^[^#]/ s/\(^.*from guesslang import Guess.*$\)/#\ \1/' app.py
sed -i '/^[^#]/ s/\(^.*guess = Guess().*$\)/#\ \1/' app.py

# Patch templates/new.html
sed -i '/^.*value="AUTO".*$/d' templates/new.html

# Patch requirements.txt
sed -i '/^[^#]/ s/\(^.*guesslang.*$\)/#\ \1/' requirements.txt
