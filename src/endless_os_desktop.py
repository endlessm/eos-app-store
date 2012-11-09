#!/usr/bin/env python
from desktop_builder import build_desktop
from startup.initial_tasks import InitialTasks
from startup.startup_tasks import StartupTasks

if __name__ == "__main__":
	InitialTasks().perform_tasks()
	StartupTasks().perform_tasks()

	build_desktop()
