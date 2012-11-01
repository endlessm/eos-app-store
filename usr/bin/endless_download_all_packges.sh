#!/bin/bash -e

sudoapt-get -y -d -o Dir::Cache::Archives=$ENDLESS_DOWNLOAD_DIRECTORY install endless*
