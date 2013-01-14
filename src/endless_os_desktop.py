import sys

if __name__ == "__main__":
	InitialTasks().perform_tasks()
	StartupTasks().perform_tasks()

	build_desktop()
   
   gobject.threads_init()
   gtk.threads_init()
   gtk.main()
