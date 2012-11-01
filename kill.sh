#!/bin/bash

ps -ef | grep endless_os_desktop | grep -v grep | awk '{print $2}' | xargs kill -9
