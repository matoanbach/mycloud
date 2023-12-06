Before running the server, we need to run the test to make everything is in the right place. This can be done by doing so: <br>
Note: in this assignment, we will use unittest library just for ease. The library is basically a built-in library in Django. So, no installation required. However, if you don't see Django and unittest installed in your computer, please proceed to install them<br>
step 1: run command "cd mycloud" <br>
step 2: run command "python3 manage.py test". Note: to spin the server, every OS will have a different to do so, please research how to do it corresponding with your OS <br>
<br>
<br>
<br>
We will use pytest library to generate a report for the test we just did. In order to do this, you need to: <br>
Step 1: install pytest using "python3 -m pip install pytest pytest-django"
Step 2: create pytest.ini in the root folder and then copy these line:

```
# pytest.ini
[pytest]
DJANGO_SETTINGS_MODULE = mycloud.settings
python_files = 'cloud/tests/tests.py'
addopts = -v --tb=line --html=report.html
```
Read this github article: https://www.nobledesktop.com/learn/git/git-branches. This link includes quite enough git command. <br>

After reading, you can proceed as follow:<br>
step 1: download and unzip the repository<br>
step 2: go to your terminal and cd over the file that you just downloaded by using command: cd main (windows might be different)<br>
step 3: go to github and then create a new branch<br>
step 4: go back to your terminal and run: git branch -r --> this is to list all remote branch, if<br>
you dont see your branch that you just created, you may have to repeat step 3<br>
step 5: now run: find . -path "_/migrations/_.py" -not -name "**init**.py" -delete<br>
find . -path "_/migrations/_.pyc" -delete<br>
--> this is to delete my migrations file (everyone might have a different migration that works for different computers)<br>
step 6: navigate to settings.py and change your database<br>
```
DATABASES = {
    'default': {
    'ENGINE': 'django.db.backends.postgresql_psycopg2',
    'NAME': 'your database name', 
    'USER': 'your user name',
    'PASSWORD': 'your password',
    'HOST': '127.0.0.1', 
    'PORT': '5432',<
    }
}
```
step 7: run command: python manage.py makemigrations<br>
python manage.py migrate<br>
step 8: spin up the server: python manage.py server<br>
