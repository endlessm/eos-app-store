#!/usr/bin/env python
from desktop_builder import build_desktop
from startup.tasks import Tasks

if __name__ == "__main__":
	Tasks().perform_startup_tasks()

	build_desktop()
    
