Tead this github article: https://www.nobledesktop.com/learn/git/git-branches. This link includes quite enough git command. <br>
After reading, you can proceed as follow:<br>
step 1: download and unzip the repository<br>
step 2: go to your terminal and cd over the file that you just downloaded by using command: cd main (windows might be different)<br>
step 3: go to github and then create a new branch<br>
step 4: go back to your terminal and run: git branch -r --> this is to list all remote branch, if<br>
        you dont see your branch that you just created, you may have to repeat step 3<br>
step 5: now run:   find . -path "*/migrations/*.py" -not -name "__init__.py" -delete<br>
                   find . -path "*/migrations/*.pyc"  -delete<br>
                   --> this is to delete my migrations file (everyone might have a different migration that works for different computers)<br>
step 6: navigate to settings.py and change your database<br>
      DATABASES = {<br>
        'default': {<br>
        'ENGINE': 'django.db.backends.postgresql_psycopg2',<br>
        'NAME': 'your database name', <br>
        'USER': 'your user name',<br>
        'PASSWORD': 'your password',<br>
        'HOST': '127.0.0.1', <br>
        'PORT': '5432',<br>
    }<br>
}<br>
step 7: run command:  python manage.py makemigrations<br>
                      python manage.py migrate<br>
step 8: spin up the server: python manage.py server<br>
