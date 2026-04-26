
# to run website you will need to need to 
# 1) install django by typing 'pip install django' in the vscode termainl 
# 2) type the following in the terminal: 
#       cd src/frontend 
#       python manage.py runserver
# 4) in chrome type: http://127.0.0.1:8000/  to look at the website 
# 5) when the terminal is running you can type c + cntrl to break it out 

# to access the backend python code form the front end   
# need to install fastapi ivicorn by typing 'pip install fastapi uvicorn' in the vscode termainl


import os
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mywebsite.settings')

from django.core.management import execute_from_command_line

execute_from_command_line(sys.argv)