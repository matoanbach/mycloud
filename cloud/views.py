from django.shortcuts import render, redirect, get_list_or_404
from django.http import HttpResponse, HttpResponseRedirect
from .forms import FileForm, RegisterForm, ShareForm
from .models import Files, User, Shared
from cloud.utils.password_utils import hash_password, check_password
from cloud.utils.token_utils import create_jwt, verify_jwt
from cloud.utils.env_key_getter import get_key
from cloud.utils.cryption import encrypt_data, decrypt_data


# Create your views here.


def index(request):
    # get the current cookie session
    token = request.COOKIES.get("token")
    if token == None:
        return redirect("/cloud/login")
    payload = verify_jwt(token)
    # get the current user's profile from database using the token payload
    try:
        cookied_user = User.objects.get(pk=payload["user_id"])
    except User.DoesNotExist:
        return HttpResponse("""<h1>User not found <a href="/cloud/login">Login</a><h1>""")

    # get the admin's profile from database
    try:
        admin = User.objects.get(email="admin@gmail.com")
    except User.DoesNotExist:
        admin = None
        return HttpResponse("""<h1>Admin not found <a href="/cloud/login">Login</a><h1>""")

    # verify the current user with admin - redirect to the login page if they're not authenticated
    if admin.email != cookied_user.email or admin.id != cookied_user.id:
        return HttpResponse("""<h1>You are not authorized to access this page. Please<a href="/cloud/login"> login </a> with your admin account<h1>""")

    # if the current user is authorized, display all the users and files uploaded
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


def upload(request):
    token = request.COOKIES.get("token")
    if token == None:
        return redirect("/cloud/login")
    payload = verify_jwt(token)

    try:
        cookied_user = User.objects.get(pk=payload["user_id"])
    except User.DoesNotExist:
        cookied_user = None

    if cookied_user == None:
        return redirect("/cloud/login")

    if request.method == "POST":
        form = FileForm(request.POST, request.FILES)

        if form.is_valid():
            developer_password = get_key("DEVELOPER_PASSWORD")
            title = form.cleaned_data["title"]
            file = form.cleaned_data["file"].file.read()
            name = form.cleaned_data["file"].name
            size = form.cleaned_data["file"].size
            file_name = form.cleaned_data["file"].size
            charset = form.cleaned_data["file"].charset

            content_type = form.cleaned_data["file"].content_type
            print(name, content_type)
            encrypted_file = encrypt_data(file, developer_password)
            new_file = Files.objects.create(
                title=title, file=encrypted_file, created_by=cookied_user, name=name, content_type=content_type, size=size, file_name=file_name, charset=charset)
            return redirect('/cloud')
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


def share(request, file_id):
    # Authentication and authorization process for this route:
    # The current user in the existing cookie session is needed to be compared with the file's owner
    # Appropriately handling if the targeted file is not from the same user or creator

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

            new_shared_file = Shared.objects.create(  # create a relationship between users who shared files - display an successful message afterwards
                shared_user=shared_user, shared_file=shared_file)
            return HttpResponse(("""<h1>File shared successfully<h1>"""))
    return render(request, "share.html", context)


def download(request, file_id):
    # Authentication and authorization process for this route:
    # The current user in the existing cookie session is needed to be compared with the file's owner
    # Appropriately handling if the targeted file is not from the same user or creator

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

    # check whether the owner of the file is the current user, if not, display a message
    if file.created_by.id != cookied_user.id:
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

    encrypted_file = file.file.tobytes().decode()
    decrypted_file = decrypt_data(encrypted_file, developer_password)

    response = HttpResponse(
        decrypted_file, content_type="application/octet-stream")
    response['Content-Disposition'] = f'inline; filename="{file.name}"'
    return response


def register(request):
    context = None
    # The form provides necessary fields (name, email, password) for creating a new user
    # A new user with the same email will not be allowed
    # The password provided by the user is hashed with a developer key before storing it in the database

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

        hashed_password = hash_password(password)
        new_user = User.objects.create(
            name=name, email=email, password=hashed_password)
        return redirect("/cloud/login")
    return render(request, "register.html")


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
