from ..models import User, Files, Shared
from cloud.utils.cryption import encrypt_data, decrypt_data
from cloud.utils.env_key_getter import get_key
from django.http import HttpResponse, HttpResponseRedirect


def register_user(name, email, password):
    new_user = User.objects.create(
        name=name, email=email, password=password)
    return new_user


def upload_file(title, file, cookied_user, name, content_type, size, file_name, charset):
    developer_password = get_key("DEVELOPER_PASSWORD")
    encrypted_file = encrypt_data(file, developer_password)

    new_file = Files.objects.create(
        title=title, file=encrypted_file, created_by=cookied_user, name=name, content_type=content_type, size=size, file_name=file_name, charset=charset)
    return new_file


def download_file(file):
    developer_password = get_key("DEVELOPER_PASSWORD")
    encrypted_file = file.file.tobytes().decode()
    decrypted_file = decrypt_data(encrypted_file, developer_password)

    return decrypted_file


def share_file(shared_user, shared_file):
    new_shared_file = Shared.objects.create(  # create a relationship between users who shared files - display an successful message afterwards
        shared_user=shared_user, shared_file=shared_file)
