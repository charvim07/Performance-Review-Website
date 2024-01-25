import unittest
from webtest import TestApp
import main
import sqlite3


class TestMyApp(unittest.TestCase):
    def setUp(self):
        # Create a TestApp instance for the Bottle app
        self.app = TestApp(main.app)
        self.base_url = 'http://localhost:80'
        self.user = main.get_user('Shima')  # Sample user for testing

    def tearDown(self):
        # Clean up the database (delete the user created during the test)
        username = 'NewUser'
        self.delete_user_from_database(username)

    def delete_user_from_database(self, username):
        """
        Delete the specified user from the database.

        Parameters:
            username (str): The username of the user to be deleted.
        """
        try:
            conn = sqlite3.connect('Comp2005.db')  # Update with your actual database path
            cursor = conn.cursor()
            delete_query = "DELETE FROM UserProfile WHERE Username = ?"
            cursor.execute(delete_query, (username,))
            conn.commit()
            conn.close()
        except sqlite3.Error as e:
            print(f"SQLite error: {e}")
            raise e

    def create_test_user(self, username, password):
        # Add the test user to the existing database
        main.update_password(username, password)

    def get_user_password(self, username):
        # Retrieve the password for the given username from the existing database
        user_info = main.get_user(username)
        return user_info.password if user_info else None

    def test_login_successful(self):
        # Test a successful login
        response = self.app.post('/login', {'username': self.user.username, 'password': self.user.password})
        expected_url = f'{self.base_url}/homepage'
        self.assertEqual(response.status_int, 303)  # Expect a redirect status code (303 instead of 302)
        self.assertEqual(response.location, expected_url)  # Expect a redirect to the homepage

    def test_login_invalid_credentials(self):
        # Test login with invalid credentials
        response = self.app.post('/login', {'username': self.user.username, 'password': 'invalid_password'})
        self.assertEqual(response.status_int, 200)  # Expect a status code indicating a failed login
        self.assertIn(b"Invalid username or password. Please try again.", response.body)  # Expect an error message

    def test_login_nonexistent_user(self):
        # Test login for a user that doesn't exist
        response = self.app.post('/login', {'username': 'nonexistent_user', 'password': self.user.password})
        self.assertEqual(response.status_int, 200)  # Expect a status code indicating a failed login
        self.assertIn(b"User with username", response.body)  # Expect an error message about the user not existing

    def test_submit_review(self):
        # Simulate a POST request to submit a review
        data = {
            'review': 'This is a test review',
            'reviewer_name': self.user.username,
            'review_for': 'Jonathan',
        }
        response = self.app.post('/addreview', data)

        # Check if the response is as expected
        self.assertEqual(response.status_int, 200)

        # Verify that the review is inserted into the database
        review_entry = main.get_review_data('Shima')
        self.assertIsNotNone(review_entry['Jonathan'])  # Ensure the review is in the database for 'Jonathan'

    def test_save_review(self):
        data = {
            'action': 'save',
            'review': 'This is a test review',
            'reviewer_name': 'Jonathan',
            'review_for': 'Shima'
        }
        response = self.app.post('/draftreview', data)
        self.assertEqual(response.status_int, 200)
        saved_reviews = main.get_review_data('Shima')
        self.assertIsNotNone(saved_reviews['Jonathan'])  # Ensure the saved review is in the database for 'Jonathan'

    def test_user_page(self):
        data = {'title': self.user.username,
                'name_list': ['Jonathan', 'Charvi', 'Adit', 'Shima', 'Dhruvin'],
                'review_data': main.get_review_data(self.user.username),
                'role': '',
                'location': '',
                'email': '',
                'skills_and_level_combined': []
                }
        response = self.app.get(f'/user?title={self.user.username}', params=data)
        self.assertEqual(response.status_int, 302)
        # Check if certain elements are present in the response
        self.assertIn(b'', response.body)

    def test_search(self):
        response = self.app.get('/search', {'query': 'example'})
        self.assertEqual(response.status_int, 200)
        self.assertIn(b'Another <span class=\'highlight\'>example</span> of content.', response.body)

    def test_delete_draft_review(self):
        # Create a draft review in the database for testing
        conn = sqlite3.connect('Comp2005.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Draft (Review, WrittenBy, ReviewFor) VALUES (?, ?, ?)",
                       ("Test draft review", "Shima", "Jonathan"))
        conn.commit()
        conn.close()

        # Simulate a POST request to delete the draft review
        data = {
            'action': 'delete',
            'reviewer_name': 'Shima',
            'review_for': 'Jonathan',
        }
        response = self.app.post('/draftreview', data)

        # Check if the response is as expected
        self.assertEqual(response.status_int, 200)

        # Verify that the draft review is deleted from the database
        conn = sqlite3.connect('Comp2005.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM Draft WHERE WrittenBy=? AND ReviewFor=?", ("Shima", "Jonathan"))
        row = cursor.fetchone()
        conn.close()

        # Ensure that the draft review is deleted (row should be None)
        self.assertIsNone(row)

    def test_add_review_page(self):
        # Simulate a GET request to the add review page
        response = self.app.get('/addreview.html')

        # Check if the response is as expected
        self.assertEqual(response.status_int, 200)
        self.assertIn(b'Submit a review here', response.body)  # Ensure the add review page is rendered

    def test_sign_up(self):
        # Simulate a POST request to sign up a new user
        data = {
            'username': 'NewUser',
            'fname': 'New',
            'lname': 'User',
            'pass1': 'password123',
            'pass2': 'password123',
            'student_id': '987654321',
        }
        response = self.app.post('/signup', data)

        # Check if the response is as expected
        self.assertEqual(response.status_int, 200)

        # Verify that the new user is added to the database
        new_user_password = self.get_user_password('NewUser')
        self.assertIsNotNone(new_user_password)  # Ensure the new user is added

    def test_update_settings(self):
        # Simulate a POST request to update user settings
        data = {
            'username': self.user.username,
            'firstname': 'NewFirstName',
            'lastname': 'NewLastName',
            'studentid': '123456789',
            'useremail': 'newemail@example.com',
        }
        response = self.app.post('/update_settings', data)

        # Check if the response is as expected
        self.assertEqual(response.status_int, 200)

        # Verify that the user information is updated in the database
        updated_user_info = main.get_user(self.user.username)
        self.assertEqual(updated_user_info.firstname, 'NewFirstName')  # Ensure firstname is updated
        self.assertEqual(updated_user_info.lastname, 'NewLastName')  # Ensure lastname is updated
        self.assertEqual(updated_user_info.studentid, '123456789')  # Ensure studentid is updated
        self.assertEqual(updated_user_info.useremail, 'newemail@example.com')  # Ensure useremail is updated

    def test_reset_password(self):
        # Simulate a POST request to reset the password
        data = {
            'username': 'Shima',
            'new': 'new_password',
            'confirm': 'new_password',
        }
        response = self.app.post('/reset_password', data)

        # Check if the response is as expected
        self.assertEqual(response.status_int, 200)

        # Verify that the password is updated in the database
        updated_password = self.get_user_password('Shima')
        self.assertEqual(updated_password, 'new_password')  # Ensure the password is updated

    def test_update_settings(self):
        # Simulate a POST request to update user settings
        data = {
            'username': self.user.username,
            'firstname': 'NewFirstName',
            'lastname': 'NewLastName',
            'studentid': '123456789',
            'useremail': 'newemail@example.com',
        }
        response = self.app.post('/update_settings', data)

        # Check if the response is as expected
        self.assertEqual(response.status_int, 200)

        # Verify that the user information is updated in the database
        updated_user_info = main.get_user(self.user.username)
        self.assertEqual(updated_user_info.firstname, 'NewFirstName')  # Ensure firstname is updated
        self.assertEqual(updated_user_info.lastname, 'NewLastName')  # Ensure lastname is updated
        self.assertEqual(updated_user_info.studentid, '123456789')  # Ensure studentid is updated
        self.assertEqual(updated_user_info.useremail, 'newemail@example.com')  # Ensure useremail is updated

    def logout_test(self):
        response = self.app.get('/')
        self.assertEqual(response.status_int, 200)
        self.assertIn("Logout out Successful", response.body)

    def setUp_new(self):
        self.app = self.app.test_client()
        self.app.testing = True
        # Create a test database in memory or use a test database file
        self.db = sqlite3.connect(':memory:')
        with self.db:
            with self.db.cursor() as cursor:
                cursor.execute(
                    'CREATE TABLE UserProfile (UserID INTEGER PRIMARY KEY, UserName TEXT, Password TEXT, FirstName TEXT, LastName TEXT, StudentID TEXT)')
                # Insert a sample user to test existing username validation
                cursor.execute(
                    'INSERT INTO UserProfile (UserID, UserName, Password, FirstName, LastName, StudentID) VALUES (?, ?, ?, ?, ?, ?)',
                    (1, 'existing_username', 'password123', 'John', 'Doe', 'S12345'))

    def test_get_signup_route(self):
        response = self.app.get('/signup')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'<title>Signup</title>', response.data)

    def test_post_signup_route_username_exists(self):
        data = {
            'username': 'Dhruvin', 'fname': 'dhruvin', 'lname': 'shah', 'student_id': '123456', 'pass1': '123', 'pass2': '123'

        }
        response = self.app.post('/signup', data=data, follow_redirects=True)
        self.assertIn(b'Username already exists', response.data)
        # Check that the user was not added to the database
        with self.db.cursor() as cursor:
            cursor.execute('SELECT COUNT(*) FROM UserProfile WHERE UserName = ?', ('existing_username',))
            count = cursor.fetchone()[0]
            self.assertEqual(count, 1)


if __name__ == '__main__':
    unittest.main()
