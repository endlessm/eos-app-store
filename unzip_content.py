#!/usr/bin/python

# To use this script, first log into eoscms.parafernalia.net.br
# Under "App Store", click on "Generate Package"
# There should be no warnings
# Click on "Click here to download files in zip format"
# Save the downloaded file in this folder as appstore.zip
# Run this script
# Add and commit any changes to git
# Proceed with the normal build process

import json
import os
import shutil
import sys
import zipfile

ZIP_FILENAME = 'appstore.zip'
UNZIP_DIR = 'unzipped'
CONTENT_DIR = 'content/Default'
IGNORE_ERRORS = True

# Remove a file if it exists; ignore errors
def delete_file(path):
    try:
        os.remove(path)
    except:
        pass

# Remove the existing unzipped and content directories, if they exist
shutil.rmtree(UNZIP_DIR, IGNORE_ERRORS)
shutil.rmtree(CONTENT_DIR, IGNORE_ERRORS)

# Unzip the file
zfile = zipfile.ZipFile(ZIP_FILENAME)
zfile.extractall(UNZIP_DIR)

# Copy the app json to the content folder
source = os.path.join(UNZIP_DIR, 'apps', 'content.json')
target_dir = os.path.join(CONTENT_DIR, 'apps')
target = os.path.join(target_dir, 'content.json')
os.makedirs(target_dir)
shutil.copy(source, target)

# Copy the thumbnail images to the content folder
source_dir = os.path.join(UNZIP_DIR, 'apps', 'thumbs')
target_dir = os.path.join(CONTENT_DIR, 'apps', 'resources', 'thumbnails')
os.makedirs(target_dir)
for source in os.listdir(source_dir):
    target = source
    shutil.copy(os.path.join(source_dir, source),
                os.path.join(target_dir, target))

# Copy the featured images to the content folder
# (Note: if the featured image is square, we just use the thumbnail)
source_dir = os.path.join(UNZIP_DIR, 'apps', 'featured')
target_dir = os.path.join(CONTENT_DIR, 'apps', 'resources', 'images')
os.makedirs(target_dir)
for source in os.listdir(source_dir):
    target = source
    shutil.copy(os.path.join(source_dir, source),
                os.path.join(target_dir, target))

# Copy the screenshot images to the content folder
# (Note: if the featured image is square, we just use the thumbnail)
source_dir = os.path.join(UNZIP_DIR, 'apps', 'screenshots')
target_dir = os.path.join(CONTENT_DIR, 'apps', 'resources', 'screenshots')
os.makedirs(target_dir)
for source in os.listdir(source_dir):
    target = source
    shutil.copy(os.path.join(source_dir, source),
                os.path.join(target_dir, target))

# Copy and rename the links json to the content folder
# We currently support only one version of the content,
# so we use the en-us and ignore es-gt and pt-br
source = os.path.join(UNZIP_DIR, 'links', 'en-us.json')
target_dir = os.path.join(CONTENT_DIR, 'links')
target = os.path.join(target_dir, 'content.json')
os.makedirs(target_dir)
shutil.copy(source, target)

# Copy the link images to the content folder
source_dir = os.path.join(UNZIP_DIR, 'links', 'images')
target_dir = os.path.join(CONTENT_DIR, 'links', 'images')
os.makedirs(target_dir)
for source in os.listdir(source_dir):
    target = source
    shutil.copy(os.path.join(source_dir, source),
                os.path.join(target_dir, target))

# Note: we currently ignore the folder icons in the icons folder
# They are .png files, where we currently need .svg files
