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

# Copy a json file with nice formatting
def json_pretty_copy(source, target):
    f = open(source, 'r')
    data = json.load(f)
    f.close()
    f = open(target, 'w')
    f.write(json.dumps(data, indent=2))
    f.close()

# Special case for app json, to work around issues in the CMS output
def json_pretty_copy_app(source, target):
    f = open(source, 'r')
    data = json.load(f)
    f.close()

    have_errors = False

    # Tweak the json content
    for app in data:
        app_id = app['application-id']

        # App IDs are not yet enforced as mandatory in CMS
        if not app_id:
            print 'Missing application-id for ' + app['title']
            have_errors = True
            continue

        # Note misspelling of 'featured_img' in CMS
        featured_img = app['fetured_img']
        del app['fetured_img']

        if featured_img == '':
            # No featured image provided
            # Code will need to use the thumbnail instead
            pass
        else:
            # Featured image provided -- fix the name
            featured_img = app_id + '-featured.jpg'
        app['featured_img'] = featured_img

        # Fix the name of the thumbnail
        app['square_img'] = app_id + '-thumb.jpg'

        # Fix 'is_featured' to be boolean
        is_featured = app['is_featured']
        if is_featured == "1":
            is_featured = True
        else:
            is_featured = False
        app['is_featured'] = is_featured

        # Fix 'is_offline' to be boolean
        is_offline = app['is_offline']
        if is_offline == "1":
            is_offline = True
        else:
            is_offline = False
        app['is_offline'] = is_offline

    if have_errors:
        sys.exit('Fatal error(s): Fix the CMS and try again')

    f = open(target, 'w')
    f.write(json.dumps(data, indent=2))
    f.close()

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

# Copy and rename the app json to the content folder
source = os.path.join(UNZIP_DIR, 'apps', 'en-us-appstore.json')
target_dir = os.path.join(CONTENT_DIR, 'apps')
target = os.path.join(target_dir, 'content.json')
os.makedirs(target_dir)
json_pretty_copy_app(source, target)

# Copy and rename the thumbnail images to the content folder
source_dir = os.path.join(UNZIP_DIR, 'apps', 'thumbs')
target_dir = os.path.join(CONTENT_DIR, 'apps', 'resources', 'thumbnails')
os.makedirs(target_dir)
for source in os.listdir(source_dir):
    # Avoid copying a leftover invalid file in the CMS
    if (source != '_thumb.jpg'):
        target = source.replace('_thumb.jpg', '-thumb.jpg')
        shutil.copy(os.path.join(source_dir, source),
                    os.path.join(target_dir, target))

# Copy the featured images to the content folder
# (Note: if the featured image is square, we just use the thumbnail)
source_dir = os.path.join(UNZIP_DIR, 'apps', 'featured')
target_dir = os.path.join(CONTENT_DIR, 'apps', 'resources', 'images')
os.makedirs(target_dir)
for source in os.listdir(source_dir):
    # Avoid copying a leftover invalid file in the CMS
    if (source != '-featured.jpg'):
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
json_pretty_copy(source, target)

# Copy the link images to the content folder
source_dir = os.path.join(UNZIP_DIR, 'links', 'images')
target_dir = os.path.join(CONTENT_DIR, 'links', 'images')
os.makedirs(target_dir)
for source in os.listdir(source_dir):
    # Remove the apostrophe character from the CMS file name
    # (Will go away once the link ID is used to generate file names)
    target = source.replace("'", '')
    shutil.copy(os.path.join(source_dir, source),
                os.path.join(target_dir, target))

# Note: we currently ignore the folder icons in the icons folder
# They are .png files, where we currently need .svg files
