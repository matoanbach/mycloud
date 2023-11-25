from django.test import TestCase
from cloud.models import User, Files, Shared
from ..utils.password_utils import hash_password
from ..utils.token_utils import create_jwt, verify_jwt
from ..utils.main_utils import register_user, upload_file, download_file, share_file
import PyPDF2
import os


class ApplicationTestCase(TestCase):
    def setUp(self):
        pass

    def test_register(self):
        test_user_name = "Test User1"
        test_user_email = "testuser1@myseneca.ca"
        test_user_password = "testuser1"
        test_user_hashed_password = hash_password(test_user_password)

        new_user = register_user(
            test_user_name, test_user_email, test_user_hashed_password)

        new_test_user = User.objects.get(email=test_user_email)

        self.assertEqual(new_test_user.name, test_user_name)
        self.assertEqual(new_test_user.email, test_user_email)
        self.assertEqual(bytes(new_test_user.password),
                         test_user_hashed_password)

    def test_login(self):
        test_user_name = "Test User1"
        test_user_email = "testuser1@myseneca.ca"
        test_user_password = "testuser1"
        test_user_hashed_password = hash_password(test_user_password)

        register_user(test_user_name, test_user_email,
                      test_user_hashed_password)

        # login the user and then give them a token credential (this is equivalent to a cookie session)
        new_test_user = User.objects.get(email=test_user_email)

        payload = {"user_id": new_test_user.id, "email": new_test_user.email}
        token = create_jwt(payload)

        # case 1: user login with a valid name and password
        test_user_email_1 = "testuser1@myseneca.ca"
        test_user_password_1 = "testuser1"
        test_user_hashed_password_1 = hash_password(test_user_password_1)
        test_user_1 = User.objects.get(email=test_user_email_1)

        verified_payload = verify_jwt(token)
        self.assertEqual(test_user_1.id, verified_payload["user_id"])
        self.assertEqual(test_user_1.email, verified_payload["email"])

        # case 2: user login with a invalid name and password
        test_user_email_2 = "testuser2@myseneca.ca"
        test_user_password_2 = "testuser2"
        test_user_hashed_password_2 = hash_password(test_user_password_2)
        try:
            test_user_2 = User.objects.get(email=test_user_email_2)
        except User.DoesNotExist:
            return

        verified_payload = verify_jwt(token)
        self.assertNotEqual(test_user_2.id, verified_payload["user_id"])
        self.assertNotEqual(test_user_2.email, verified_payload["email"])

    def test_upload_and_download(self):
        pdf_path = "/Users/bachmatoan/Library/CloudStorage/OneDrive-Seneca/Seneca/SEMESTER3/SEP300/A1/main-1/mycloud/cloud/tests/test_files/2237_BTD210_Addendum.pdf"

        test_user_name = "Test User1"
        test_user_email = "testuser1@myseneca.ca"
        test_user_password = "testuser1"
        test_user_hashed_password = hash_password(test_user_password)

        register_user(test_user_name, test_user_email,
                      test_user_hashed_password)
        # ------- UPLOAD --------
        # Test file upload functionality for authenticated users.
        # login the user and then give them a token credential (this is equivalent to a cookie session)
        new_test_user = User.objects.get(email=test_user_email)

        with open(pdf_path, "rb") as file:
            title = "test_file_1"
            read_file = file.read()
            name = "2237_BTD210_Addendum.pdf 282340"
            size = os.path.getsize(file.name)
            file_name = os.path.getsize(file.name)
            charset = None
            content_type = "application/pdf"
            upload_file(title, read_file, new_test_user, name,
                        content_type, size, file_name, charset)

            new_file = Files.objects.get(name=name, created_by=new_test_user)
        # Ensure files are encrypted using symmetric encryption (e.g., AES)during upload.
        # If the file uploaded from the user is different from the one in database,
        # it means that the file is converted to an unreadable format
        self.assertNotEqual(new_file.file.tobytes(), read_file)

        # The other information should be matching with the one in database
        self.assertEqual(new_file.title, title)
        self.assertEqual(new_file.name, name)
        self.assertEqual(new_file.size, size)
        self.assertEqual(int(new_file.file_name), file_name)
        self.assertEqual(new_file.content_type, content_type)

        # ------- DOWNLOAD --------
        # Confirm that users can download their own uploaded files securely.
        # The file needed to download is important to be under readable format
        # where it is decrypted before the user downloads it

        # the current user gets the file from the database
        fetched_file = Files.objects.get(name=name, created_by=new_test_user)
        decrypted_file = download_file(fetched_file)
        self.assertEqual(decrypted_file, read_file)

        # ------- Download with unauthorized access ------
        # Verify proper handling of unauthorized access attempts during file download.
        test_user_name_2 = "Test User2"
        test_user_email_2 = "testuser2@myseneca.ca"
        test_user_password_2 = "testuser2"
        new_file = Files.objects.get(name=name)
        self.assertNotEqual(new_file.created_by.email, test_user_email_2)


    def test_sharing_files(self):
        pdf_path = "/Users/bachmatoan/Library/CloudStorage/OneDrive-Seneca/Seneca/SEMESTER3/SEP300/A1/main-1/mycloud/cloud/tests/test_files/2237_BTD210_Addendum.pdf"
        
        test_user_name_1 = "Test User 1"
        test_user_email_1 = "testuser1@myseneca.ca"
        test_user_password_1 = "testuser1"
        test_user_hashed_password_1 = hash_password(test_user_password_1)
        user1 = register_user(test_user_name_1, test_user_email_1,
                      test_user_hashed_password_1)
        
        test_user_name_2 = "Test User 2"
        test_user_email_2 = "testuser2@myseneca.ca"
        test_user_password_2 = "testuser2"
        test_user_hashed_password_2 = hash_password(test_user_password_2)
        user2 = register_user(test_user_name_2, test_user_email_2,
                      test_user_hashed_password_2)
        
        test_user_name_3 = "Test User 3"
        test_user_email_3 = "testuser3@myseneca.ca"
        test_user_password_3 = "testuser3"
        test_user_hashed_password_3 = hash_password(test_user_password_3)
        user3 = register_user(test_user_name_3, test_user_email_3,
                      test_user_hashed_password_3)


        with open(pdf_path, "rb") as file:
            title = "test_file_1"
            read_file = file.read()
            name = "2237_BTD210_Addendum.pdf 282340"
            size = os.path.getsize(file.name)
            file_name = os.path.getsize(file.name)
            charset = None
            content_type = "application/pdf"
            upload_file(title, read_file, user1, name,
                        content_type, size, file_name, charset)

            shared_file = Files.objects.get(name=name, created_by=user1)

            # Test the secure mechanism for users to share files with specific other users.
            # user 1 is sharing the file with user 2
            new_shared_file = share_file(user2, shared_file)


            # Confirm that only authorized users can access shared files.
            # check if the file is shared successfully
            found_new_shared_file = Shared.objects.get(shared_user=user2, shared_file=shared_file)
            self.assertEqual(found_new_shared_file.shared_file, shared_file)
            

            # Verify that unauthorized users are unable to access shared files
            # user 3 should not be able to access the file
            try:
                found_new_shared_file = Shared.objects.get(shared_user=user3, shared_file=shared_file)
            except Shared.DoesNotExist:
                found_new_shared_file = None

            self.assertNotEqual(shared_file, found_new_shared_file)

    # def test_execution(self):
    #     # Configure Pytest to generate detailed test reports.
    #     # Ensure that your test reports provide valuable insights into test results,including any failures or errors.
    #     # Use Pytest's reporting features to identify areas for improvement in yourcode
    #     # You should be achieving 8/10 on pytest score
    #     pass
