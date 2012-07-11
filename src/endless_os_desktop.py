#!/usr/bin/env python
from desktop.endless_desktop_presenter import DesktopPresenter
from desktop.endless_desktop_view import EndlessDesktopView

if __name__ == "__main__":
    presenter = DesktopPresenter(EndlessDesktopView())
    presenter._view.main()
