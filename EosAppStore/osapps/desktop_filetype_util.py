from xdg import DesktopEntry

class DesktopFiletypeUtil():
	def get_executable(self, app_name):
		execution = ""
		for param in self._get_desktop_entry(app_name).getExec().split(" "):
			if not param.startswith('%'):
				execution += param + " "
		
		return execution.strip()
	
	def get_display_name(self, app_name):
		entry = self._get_desktop_entry(app_name)
		return entry.getGenericName() if len(entry.getGenericName()) != 0 else entry.getName()
	
	def _get_desktop_entry(self, app_name):
		entry = DesktopEntry.DesktopEntry()
		entry.parse("/usr/share/applications/" + app_name)
		return entry