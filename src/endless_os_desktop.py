#!/usr/bin/env python
from desktop_builder import build_desktop
from startup.initial_tasks import InitialTasks

if __name__ == "__main__":
	InitialTasks().perform_startup_tasks()

	build_desktop()
