from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from .forms import FileForm, RegisterForm, ShareForm 
from .models import Files, User, Shared
from cloud.utils.password_utils import hash_password, check_password    # bcrypt is used to hash password
from cloud.utils.token_utils import create_jwt, verify_jwt              # jwt is used to create a cookie session
from cloud.utils.env_key_getter import get_key                          # get_key is used to access the developer's keys
from cloud.utils.cryption import encrypt_data, decrypt_data             # cryptography library is used to encrypt and decrypt data
from cloud.utils.main_utils import register_user, upload_file, download_file, share_file

# Index will have cookie verification process
# Index route is chosen to be an admin page where only admin 
#   can have the sore access to this route.
# A list of registered users and all the files uploaded are shown here. 
# Any access without authenticating will be redirected to login page
# A user with an authorized access will see a warning message
def index(request):

    # get the current cookie session
    token = request.COOKIES.get("token")
    if token == None: # check if the toke is not present, 
                      # redirect to the login page if there is no cookie with token key is available
        return redirect("/cloud/login")
    payload = verify_jwt(token) #verify the JWT token to get payload (user information)
    
    # get the current user's profile from database using the token payload
    # if the user is not found, display an error message with a link to the login page
    try:
        cookied_user = User.objects.get(pk=payload["user_id"])
    except User.DoesNotExist:
        return HttpResponse("""<h1>User not found <a href="/cloud/login">Login</a><h1>""")

    # get the admin's profile from database
    # Redirect the current user to the login page if there is no admin found yet.
    try:
        admin = User.objects.get(email="admin@gmail.com")
    except User.DoesNotExist:
        admin = None
        return HttpResponse("""<h1>Admin not found <a href="/cloud/login">Login</a><h1>""")

    # verify the current user with admin - redirect to the login page if they're not authenticated
    if admin.email != cookied_user.email or admin.id != cookied_user.id:
        return HttpResponse("""<h1>You are not authorized to access this page. Please<a href="/cloud/login"> login </a> with your admin account<h1>""")

    # if the current user is authorized to be the admin, display all the users and files uploaded
    try:
        users = User.objects.filter()
    except User.DoesNotExist:
        users = None

    try:
        files = Files.objects.filter()
    except Files.DoesNotExist:
        files = None

    return render(request, "index.html", {
        "admin": admin, "users": users, "files": files, "user_num": len(users), "file_num": len(files)
    })

# Upload will have cookie authentication process
# Upload is where users can upload data under file format through form class,
#   at which point the server will initialize an object (with data from the form) to store
#   it in the database
# Uploaded file has to be under bytes format
# Uploaded file has to be encrypted and stored in the database 
#   and a successful message displayed to indicate it stored successfully
def upload(request):

    # get the current cookie session
    token = request.COOKIES.get("token")
    if token == None:   # check if the toke is not present,
                        # redirect to the login page if there is no cookie with token key is available
        return redirect("/cloud/login")
    payload = verify_jwt(token) # verify the JWT token to get payload (user information)

    # get the current user's profile from database using the token payload
    # if the user is not found, display an error message with a link to the login page
    try:
        cookied_user = User.objects.get(pk=payload["user_id"])
    except User.DoesNotExist:
        return HttpResponse("""<h1>User not found <a href="/cloud/login">Login</a><h1>""")

    if request.method == "POST":
        form = FileForm(request.POST, request.FILES)

        # Get neccessary data from form class and then initialize an object to store the file in the data
        if form.is_valid():
            developer_password = get_key("DEVELOPER_PASSWORD")
            title = form.cleaned_data["title"]
            file = form.cleaned_data["file"].file.read()  # Encryption EAS requires the file to be under byte formate
            name = form.cleaned_data["file"].name
            size = form.cleaned_data["file"].size
            file_name = form.cleaned_data["file"].size
            charset = form.cleaned_data["file"].charset
            content_type = form.cleaned_data["file"].content_type

            new_file = upload_file(title, file, cookied_user, name, content_type, size, file_name, charset)

            return redirect('/cloud/file_list')
    else:
        form = FileForm()
    return render(request, 'upload.html', {
        "form": form
    })


def file_list(request):
    # get the current cookie session
    token = request.COOKIES.get("token")
    if token == None:
        return redirect("/cloud/login")
    payload = verify_jwt(token)

    # get the current user's profile from database using the token payload
    try:
        cookied_user = User.objects.get(pk=payload["user_id"])
    except User.DoesNotExist:
        cookied_user = None

    # redirect the user to the login page if they are not authenticated
    if cookied_user == None:
        return redirect("/cloud/login")

    # if the current user is authorized, display all files uploaded
    try:
        files = Files.objects.filter(created_by=cookied_user.id)
    except User.DoesNotExist:
        files = None
    try:
        shared_files = Shared.objects.filter(shared_user=cookied_user.id)
    except Shared.DoesNotExist:
        shared_files = None

    if files == None:
        return HttpResponse("""<h1>No file found yet <a href="upload">Upload something here</a><h1>""")
    return render(request, "file_list.html", {
        "files": files, "shared_files": shared_files, "file_num": len(files), "shared_file_num": len(shared_files)
    })

# Cookie authentication and authorization process for this route will be necessary for this route:
# The current user in the existing cookie session is needed to be compared with the file's owner
# Appropriately handling if the targeted file is not created by the same user or creator
# Appropriately handling if the targeted file is not shared for the same user or creator

def share(request, file_id):
    
    # get the current cookie session
    token = request.COOKIES["token"]
    if token == None:
        return redirect("/cloud/login")
    payload = verify_jwt(token)

    # get the current user's profile from database using the token payload
    try:
        cookied_user = User.objects.get(pk=payload["user_id"])
    except User.DoesNotExist:
        cookied_user = None

    # get the shared file from the database
    try:
        shared_file = Files.objects.get(pk=file_id)
    except Files.DoesNotExist:  # if the file does not exist, display an error page
        shared_file = None
        message = f"No such file found with id {file_id}"
        context = {
            "message": message
        }
        return render(request, "error.html", context)

    # check whether the owner of the file is the current user, if not, display an error page
    if shared_file.created_by.id != cookied_user.id:
        message = f"No such file found with id {file_id}"
        context = {
            "message": message
        }
        return render(request, "error.html", context)
    context = {"file": shared_file}

    # After done with authentication and authorization process, we proceed with this part:
    # The targeted user has to exist in the database and, the owner and targeted user have to be different (shared files with same users not allowed)
    if request.method == "POST":
        form = ShareForm(request.POST)
        if form.is_valid():
            # get the user's input from form
            # get the targeted user's profile from the database
            email = form.cleaned_data["email"]
            try:
                shared_user = User.objects.get(email=email)
            except User.DoesNotExist:  # render the error page if the user does not exist
                shared_user = None
                message = f"User does not exist"
                context = {
                    "message": message
                }
                return render(request, "error.html", context)

            # check if the user is trying to share the file with themselves
            if cookied_user.id == shared_user.id and cookied_user.name == shared_user.name:
                message = f"Share files between the same users not allowed"
                context = {
                    "message": message
                }
                return render(request, "error.html", context)

            new_shared_file = share_file(shared_user, shared_file)
            return HttpResponse(("""<h1>File shared successfully <a href="/cloud/file_list">See all files</a><h1>"""))
    return render(request, "share.html", context)

# Download has cookie authentication and authorization process for this route:
# The current user in the existing cookie session is needed to be compared with the file's owner
# Appropriately handling if the targeted file is not from the same user or creator
def download(request, file_id):
    
    # get the current cookie session
    token = request.COOKIES["token"]
    if token == None:
        return redirect("/cloud/login")
    payload = verify_jwt(token)

    # get the current user's profile from database using the token payload
    try:
        cookied_user = User.objects.get(pk=payload["user_id"])
    except User.DoesNotExist:
        cookied_user = None

    # get the file from the database
    try:
        file = Files.objects.get(pk=file_id)
    except Files.DoesNotExist:
        file = None
        message = f"No such file found with id {file_id}"
        context = {
            "message": message
        }
        return render(request, "error.html", context)
    
    # get the shared relationship between users with the found file
    try:
        shared_rels = Shared.objects.filter(shared_file=file)
    except Shared.DoesNotExist:
        shared_rels = None
    
    # find the shared file in the shared table
    is_found_shared_file = False
    if shared_rels != None:
        for shared_rel in shared_rels:
            if shared_rel.shared_user.id == cookied_user.id:
                file = shared_rel.shared_file
                is_found_shared_file = True
                break

    # check whether the owner of the file is the current user, if not, display a message
    if file.created_by.id != cookied_user.id and not is_found_shared_file:
        message = f"No such file found with id {file_id}"
        context = {
            "message": message
        }
        return render(request, "error.html", context)

    # The key is needed to be fetched from the database, so that we can decrypt data and render it to the user
    # The file fetched from the database is in "bytes" class - it is important to decode the file before rendering it to the user
    # The file will be responded from the server under appropriate formats

    # error message will be displayed if the key does not exist
    developer_password = get_key("DEVELOPER_PASSWORD")
    if developer_password == None:
        message = f"Server error, no developer password found"
        context = {
            "message": message
        }
        return render(request, "error.html", context)

    decrypted_file = download_file(file)

    response = HttpResponse(
        decrypted_file, content_type="application/octet-stream")
    response['Content-Disposition'] = f'inline; filename="{file.name}"'
    return response

# Register is where user can create an account with name, email and password
# Password has be safely hashed with a developer key to be store in the database
# A new user with the same email will not be allowed
# The password provided by the user is hashed with a developer key before storing it in the database
def register(request):
    context = None
    if request.method == "POST":
        form = RegisterForm(request.POST)
        name = form['name'].value()
        email = form['email'].value()
        password = form['password'].value()
        try:
            found_user = User.objects.filter(email=email)
        except User.DoesNotExist:
            found_user == None

        if len(found_user) > 0:  # throw an error message if a user with an existing email already exists in the database
            return HttpResponse(f"""<h1>Email already exists please, please<a href="register"> try </a>again with a unique email</h1> """)

        # password is hashed using bcrypt library
        hashed_password = hash_password(password)
        new_user = register_user(name, email, hashed_password)
        return redirect("/cloud/login")
    return render(request, "register.html")

# Login prompt users password and email to login
# if logging in successfully, a session token is created and stored within the client side as a credential
# this token is valid for 3 hours
def login(request):
    # The form provides necessary fields (email, password) for creating a new user
    # Properly handling the unauthenticated user
    # it provides a token if the user is authenticated
    context = None
    if request.method == "POST":
        form = RegisterForm(request.POST)
        email = form['email'].value()
        password = form['password'].value()

        try:
            found_user = User.objects.get(email=email)
        except User.DoesNotExist:
            found_user = None

        hashed_password = bytes(found_user.password)
        valid_user = check_password(password, hashed_password)

        if not valid_user:
            return HttpResponse("""<h1>Wrong password or email! <a href="login">Try it again.</a><h1>""")

        payload = {"user_id": found_user.id, "email": email}
        token = create_jwt(payload)
        response = redirect("/cloud/file_list")

        expiration_time = 10800  # cookie expires in 10800 seconds (3 hours)
        response.set_cookie(
            "token", token, expires=expiration_time, httponly=True)
        return response
    return render(request, "login.html")


def logout(request):
    # Set the cookie expire and redirect the user back to the login page
    response = redirect("/cloud/login")
    expiration_time = 1  # cookie expires in 1 second
    response.set_cookie("token", "logout", httponly=True,
                        expires=expiration_time)
    return response
