#!/bin/bash

done_name=../src/ui/glade_ui_elements.py
echo "" > $done_name

for file in *.glade; do
  	filename=$(basename $file)
        filename=${filename%.*}	
	echo $filename ' = "".join(' >> $done_name
	echo '"""' >> $done_name
	echo `cat $file` >> $done_name
	echo '""")' >> $done_name
done 
