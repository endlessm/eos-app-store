Endless OS Application Store
====================

To install to /usr/share:
```
./autogen.sh --datadir=/usr/share
make
make install
```

Or to install via jhbuild:
```
./autogen.sh --prefix=$HOME/gnome/install
make
make install
```
