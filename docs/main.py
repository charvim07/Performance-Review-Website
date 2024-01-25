from bottle import run, template, request, redirect, Bottle, response
import sqlite3
from beaker.middleware import SessionMiddleware

app = Bottle()
app.debug = True

session_opts = {
    'session.type': 'file',
    'session.cookie_expires': 30,
    'session.data_dir': './data',
    'session.auto': True,
}
session_app = SessionMiddleware(app, session_opts)


class UserItems:
    """
    Represents user credentials with a username and password.
    """

    def __init__(self, username, password, firstname=None, lastname=None, studentid=None, useremail=None):
        """
        Initialize the UserItems object with username and password.

        Parameters:
        - username: A string representing the user's username.
        - password: A string representing the user's password.
        - firstname (str, optional): The user's first name.
        - lastname (str, optional): The user's last name.
        - studentid (str, optional): The user's student ID.
        - useremail (str, optional): The user's email address.
        """
        self.username = username
        self.password = password
        self.firstname = firstname
        self.lastname = lastname
        self.studentid = studentid
        self.useremail = useremail


def get_user(username):
    """
    Retrieve a user from the database by their username.

    Parameters:
    - username: A string representing the user's username.

    Returns:
    - An instance of UserItems containing the user's data.

    Raises:
    - ValueError: If the user with the specified username does not exist.
    - sqlite3.Error: If there is a database error.
    """
    global conn
    db_file = 'Comp2005.db'

    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT UserName, Password, FirstName, LastName, StudentID, UserEmail FROM UserProfile WHERE UserName = ?",
            (username,))
        row = cursor.fetchone()

        if row is None:
            raise ValueError(f"User with username '{username}' does not exist.")
        _, password, firstname, lastname, studentid, useremail = row
        user_info = UserItems(username, password, firstname, lastname, studentid, useremail)
        return user_info
        # user_info = UserItems(username=row[0], password=row[1])
        # return user_info

    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
    finally:
        if conn:
            conn.close()


@app.route('/')
def login_page():
    """
    Display the login page.

    Returns:
    - The rendered template for the login page.
    """
    return template('templates\login_template', username='', password='')


@app.route('/forgot_password')
def forgot_password_page():
    """
           Render the 'forgot_password.html' template.

           Returns:
               str: Rendered HTML content for the 'forgot_password.html' template.
       """
    return template('templates\\forgot_password.html')


@app.route('/reset_password', method='POST')
def reset_password():
    """
            Reset the user's password based on the provided form data.

        Returns:
            str: A message indicating the result of the password reset process.
        """

    username = request.forms.get('username')
    new_password = request.forms.get('new')
    confirm_password = request.forms.get('confirm')
    user_info = get_user(username)

    if user_info:
        if new_password == confirm_password:

            update_password(username, new_password)
            return "Password reset successful. You can now log in with your new password."
        else:
            return "Password and confirmation do not match. Please try again."
    else:
        return "Email not found. Please check your email address and try again."


def update_password(username, new_password):
    """
        Update the user's password in the database.

        Args:
            username (str): The username of the user whose password needs to be updated.
            new_password (str): The new password to be set for the user.
        """
    try:
        conn = sqlite3.connect('Comp2005.db')
        cursor = conn.cursor()
        update_query = "UPDATE UserProfile SET Password = ? WHERE UserName = ?"
        cursor.execute(update_query, (new_password, username))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")


@app.route('/homepage')
def homepage():
    """
    Display the homepage if the user is logged in, otherwise redirect to the login page.

    Returns:
    - The rendered template for the homepage or a redirect to the login page.
    """

    connection = sqlite3.connect('Comp2005.db')
    cursor = connection.cursor()
    cursor.execute('SELECT UserName FROM userProfile')
    results = cursor.fetchall()
    name_list = [row[0] for row in results]

    global logged_user
    unlogged_users = []
    username = request.get_cookie("account", secret="akey")
    for name in name_list:
        if name == username:
            logged_user = name
        else:
            unlogged_users.append(name)

    if username == logged_user:
        return template('templates\homepage', username=username, unlogged_users=unlogged_users)
    else:
        redirect('/')


@app.route('/addreview.html')
def add_review_page():
    """
    Display the page to add a review.

    Returns:
    - The rendered template for adding a review.
    """
    username = request.get_cookie("account", secret="akey")
    return template('templates\\addreview.html', username=username)


@app.route('/login', method='POST')
def do_login():
    """
    Handle the login form submission.

    Returns:
    - A redirect to the homepage if credentials are correct, or an error message otherwise.
    """
    username = request.forms.get('username')
    password = request.forms.get('password')
    try:
        user_info = get_user(username)
        if user_info.password == password:
            session = request.environ.get('beaker.session')
            session['username'] = username
            response.set_cookie("account", username, secret='akey', path='/')
            redirect('/homepage')
        else:
            return "Invalid username or password. Please try again."
    except ValueError as e:
        return str(e)


@app.route('/addreview', method=['POST'])
def save():
    """
    Save a review to the database based on the form action.

    Returns:
    - The rendered template for adding a review.
    """
    action = request.forms.get('action')
    username = request.get_cookie("account", secret="akey")
    if action == 'save':
        conn = sqlite3.connect('Comp2005.db')
        cursor = conn.cursor()
        review = request.forms.get('review')
        reviewer_name = request.forms.get('reviewer_name')
        review_for = request.forms.get('review_for')
        insert_query = "INSERT INTO Draft (Review, WrittenBy, ReviewFor) VALUES (?, ?, ?)"
        cursor.execute(insert_query, (review, reviewer_name, review_for))
        conn.commit()
        conn.close()
        return template('addreview.html', username=username)
    elif action == 'Add':
        conn = sqlite3.connect('Comp2005.db')
        cursor = conn.cursor()
        review = request.forms.get('review')
        reviewer_name = request.forms.get('reviewer_name')
        review_for = request.forms.get('review_for')
        effort = request.forms.get('effort')
        communication = request.forms.get('communication')
        participation = request.forms.get('participation')
        meetings = request.forms.get('meetings')
        insert_query = "INSERT INTO Review (Review, WrittenBy, ReviewFor, CommuninationRatings,EffortRatings, " \
                       "ParticipationRatings,MeetingsRatings) VALUES (?, ?, ?, ?, ?, ?,?) "
        cursor.execute(insert_query,
                       (review, reviewer_name, review_for, effort, communication, participation, meetings))
        conn.commit()
        conn.close()


def get_review_data(title):
    """
    Retrieve review data for a specific title from the database.

    Parameters:
    - title: A string representing the title of the review.

    Returns:
    - A dictionary containing the review data.
    """
    connection = sqlite3.connect('Comp2005.db')
    cursor = connection.cursor()
    namelist = ["Shima", "Jonathan", "Dhruvin", "Adit", "Charvi"]
    review_data = {}
    for name in namelist:
        try:
            cursor.execute('SELECT Review FROM Review WHERE ReviewFor = ? AND WrittenBy = ? ORDER BY ID DESC LIMIT 1',
                           (title, name))

            data = cursor.fetchall()
            review_data[name] = [row[0] for row in data]
        except Exception as e:
            print(f"Error executing the query: {e}")
    connection.commit()
    connection.close()

    return review_data


@app.route('/dislike_review', method='POST')
def dislike_review():
    review_id = request.forms.get('review_id')
    db_file = 'Comp2005.db'
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("UPDATE Review SET DISLIKE = DISLIKE + 1 WHERE ID = ?", (review_id,))
        conn.commit()
        conn.close()
        return "Review Disliked"
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return "Error disliking the review"


@app.route('/like_review', method='POST')
def like_review():
    review_id = request.forms.get('review_id')
    db_file = 'Comp2005.db'
    try:
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()
        cursor.execute("UPDATE Review SET LIKE = LIKE + 1 WHERE ID = ?", (review_id,))
        conn.commit()
        conn.close()
        return "Review Liked"
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        return "Error liking the review"


@app.route('/draftreview', method=['POST'])
def load_review():
    """
    Display the draft review page.

    Returns:
    - The rendered template for the draft review page.
    """
    return template('templates\draftreview.html')


@app.route('/draftreview', method=['GET', 'POST'])
def draft_review():
    """
    Handle the draft review actions: save, submit, and load draft reviews.

    Returns:
    - The rendered template for the draft review page with the appropriate success message.
    """
    try:
        username = request.get_cookie("account", secret='akey')
        review = ""
    except Exception as e:
        print(f"Error fetching username cookie: {e}")
        username = None
        review = ""
    success_message = ""
    reviewer_name = ""
    review_for = ""
    review = ""
    if request.method == 'POST':
        action = request.forms.get('action')
        reviewer_name = request.forms.get('reviewer_name')
        review_for = request.forms.get('review_for')

        if action == 'save':
            conn = sqlite3.connect('Comp2005.db')
            cursor = conn.cursor()
            review = request.forms.get('review')
            reviewer_name = request.forms.get('reviewer_name')
            review_for = request.forms.get('review_for')
            insert_query = "INSERT INTO Draft (Review, WrittenBy, ReviewFor) VALUES (?, ?, ?)"
            cursor.execute(insert_query, (review, reviewer_name, review_for))
            conn.commit()
            conn.close()
        elif action == 'submit':
            conn = sqlite3.connect('Comp2005.db')
            cursor = conn.cursor()
            review = request.forms.get('review')
            reviewer_name = request.forms.get('reviewer_name')
            review_for = request.forms.get('review_for')
            insert_query = "INSERT INTO Review (Review, WrittenBy, ReviewFor) VALUES (?, ?, ?)"
            cursor.execute(insert_query, (review, reviewer_name, review_for))
            conn.commit()
            conn.close()
            return template('templates\draftreview.html', success_message="Submit review saved successfully")
        elif action == 'delete':
            conn = sqlite3.connect('Comp2005.db')
            cursor = conn.cursor()
            reviewer_name = request.forms.get('reviewer_name')
            review_for = request.forms.get('review_for')
            delete_query = "DELETE FROM Draft WHERE ReviewFor = ? AND WrittenBy = ?"
            cursor.execute(delete_query, (review_for, reviewer_name))
            conn.commit()
            conn.close()
            return template('templates\draftreview.html', username=username, review='', review_for=review_for,
                            reviewer_name=reviewer_name, success_message='')
        elif action == 'load':
            conn = sqlite3.connect('Comp2005.db')
            cursor = conn.cursor()
            try:
                cursor.execute("SELECT Review FROM Draft WHERE WrittenBy=? AND ReviewFor=? ORDER BY ID DESC LIMIT 1",
                               (username, review_for))
                row = cursor.fetchone()
                if row:
                    review = row[0]
                    success_message = "Latest Draft loaded successfully."
                else:
                    success_message = "No draft found for the selected criteria."
            except sqlite3.Error as e:
                success_message = f"An error occurred: {e}"
            finally:
                conn.close()
        return template('templates\draftreview.html', username=username, review=review, review_for=review_for,
                        reviewer_name=reviewer_name, success_message=success_message)

    return template('templates\draftreview.html', success_message="")


@app.route('/search')
def search():
    """
    Perform a search on static content based on the user's query.

    Returns:
    - HTML string representing the search results.
    """
    query = request.query.query

    content_list = ["This is some text content.", "Another example of content.", "More text to search."]

    search_results = [content for content in content_list if query.lower() in content.lower()]

    search_result_html = "<ul>"
    for result in search_results:
        highlighted_result = result.replace(query, f"<span class='highlight'>{query}</span>")
        search_result_html += f"<li>{highlighted_result}</li>"
    search_result_html += "</ul>"

    return search_result_html


def check_username_exists(username):
    """
    Check if a username already exists in the database.

    Args:
        username (str): The username to check.

    Returns:
        bool: True if the username exists, False otherwise.
    """
    db_file = 'Comp2005.db'
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Execute the SQL query to retrieve data from the column of UserName
    query_for_username = "SELECT UserName FROM UserProfile"
    cursor.execute(query_for_username)

    # Fetch the data from the query
    data_from_column = cursor.fetchall()
    conn.close()

    # Check if the given username exists in the fetched data
    for row in data_from_column:
        if row[0] == username:
            return True

    return False


@app.route('/signup', method=['GET', 'POST'])
def sign_up():
    """
    Handle the signup route.

    Returns:
        str: HTML template for signup.
    """
    if request.method == 'GET':
        return template('templates\signup', messages=[])
    elif request.method == 'POST':
        # Get form data
        username = request.forms.get('username')
        fname = request.forms.get('fname')
        lname = request.forms.get('lname')
        pass1 = request.forms.get('pass1')
        pass2 = request.forms.get('pass2')
        student_id = request.forms.get('student_id')

        # Check if username already exists
        if check_username_exists(username):
            return template("templates\signup", messages=["Username already exists! Please try another username."])

        # Validate username length
        if len(username) > 20:
            return template("templates\signup", messages=["Username must be under 20 characters!"])

        # Validate if the password contain a number
        if not any(i.isdigit() for i in pass1):
            return template("signup", messages=["Passwords must contain a number, a lowercase and a upeercase!"])

        # Validate if the password contain a lowercase
        if not any(i.islower() for i in pass1):
            return template("signup", messages=["Passwords must contain a number, a lowercase and a upeercase!"])

        # Validate if the password contain a uppercase
        if not any(i.isupper() for i in pass1):
            return template("signup", messages=["Passwords must contain a number, a lowercase and a upeercase!"])

        # Validate if the password is of proper length
        if len(pass1) < 8 or len(pass1) > 20:
            return template("signup", messages=["Passwords must be between 8 and 20 characters!"])

        # Validate password match
        if pass1 != pass2:
            return template("templates\signup.html", messages=["Passwords didn't match!"])

        # Validate alphanumeric username
        if not username.isalnum():
            return template("templates\signup.html", messages=["Username must be alphanumeric!"])

        # Connect to the database
        db_file = 'Comp2005.db'
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        try:
            # Get the maximum UserID to generate a new ID
            query = "SELECT MAX(UserID) FROM UserProfile"
            cursor.execute(query)
            last_id = cursor.fetchone()[0]
            new_id = int(last_id) + 1
            data_to_insert = (new_id, username, pass1, fname, lname, student_id)

            # Insert data into UserProfile table
            query_to_add_data = "INSERT INTO UserProfile (UserID, UserName, \
            Password, FirstName, LastName, StudentID) VALUES (?,?,?,?,?,?)"
            cursor.execute(query_to_add_data, data_to_insert)
            conn.commit()
        except Exception as e:
            # Rollback the transaction in case of an error
            conn.rollback()
            print(f"Error: {e}")
            raise e
        finally:
            conn.close()

        return template('templates/login_template.html')


@app.route('/user')
def user_page():
    """
    Display the page for user

    Returns:
    - The rendered template for the logged in user.
    """
    connection = sqlite3.connect('Comp2005.db')
    cursor = connection.cursor()
    cursor.execute('SELECT UserName, UserSkills, Roles, Location, UserEmail, SkillLevel FROM UserProfile')
    results = cursor.fetchall()

    namelist = [row[0] for row in results]
    skills_uncleaned = [[row[1]] for row in results]  # Obtain uncleaned skills data from database
    roles = [row[2] for row in results]
    locations = [row[3] for row in results]
    emails = [row[4] for row in results]
    skill_level_uncleaned = [[row[5]] for row in results]

    # Code to clean the skills data
    skills = []
    for skill in skills_uncleaned:
        if skill[0] is None:
            skills.append(skill)
        else:
            skills_cleaned = skill[0].split(', ')
            skills.append(skills_cleaned)

    skill_level = []
    for level in skill_level_uncleaned:
        if level[0] is None:
            skill_level.append(level)
        else:
            skill_level_cleaned = level[0].split(', ')
            skill_level.append(skill_level_cleaned)

    username = request.get_cookie("account", secret="akey")
    if username:
        index = namelist.index(username)  # index of current user logged in
        skills_and_level_combined = []
        start_index = 0
        end = len(skills[index])
        while start_index < end:
            skill_level_tuple = (skills[index][start_index], skill_level[index][start_index])
            skills_and_level_combined.append(skill_level_tuple)
            start_index += 1

        user = get_user(username)
        review_data = get_review_data(user.username)
        review_id = {}
        return template('templates/user.html', namelist=namelist, review_data=review_data, title=username,
                        role=roles[index], location=locations[index], review_id=review_id, email=emails[index],
                        skills_and_level_combined=skills_and_level_combined)
    else:
        redirect('/')


@app.route('/settings.html')
def settings_page():
    """
    Display the settings page with the user's information.

    Returns:
        str or template: The rendered template for the settings page with the user's information.
            If the user is not logged in, it redirects to the home page.
            If there is an error retrieving user information, it returns an error message.
    """
    session = request.environ.get('beaker.session')
    username = session.get('username')

    if not username:
        redirect('/')

    try:
        user_info = get_user(username)

        if user_info:
            return template('templates\settings', username=user_info.username,
                            firstname=user_info.firstname, lastname=user_info.lastname,
                            studentid=user_info.studentid, useremail=user_info.useremail)
        else:
            return "Error: User information could not be retrieved."

    except Exception as e:
        return f"An error occurred: {e}"


@app.route('/update_settings', method='POST')
def update_settings():
    """
        Update the user's settings based on the form data.

        Returns:
            str: A success message if the update is successful.

        Raises:
            HTTPResponse: If there is an error during the update, sets an appropriate HTTP status code.
        """
    try:
        session = request.environ.get('beaker.session')
        username = session.get('username')

        # Retrieve user information from the form
        firstname = request.forms.get('firstname')
        lastname = request.forms.get('lastname')
        studentid = request.forms.get('studentid')
        useremail = request.forms.get('useremail')

        # Update the user information in the database
        update_user_info(username, firstname, lastname, studentid, useremail)

        return "Information has been successfully updated."
    except Exception as e:
        response.status = 500  # Set an appropriate HTTP status code for error
        return f"An error occurred: {e}"


def update_user_info(username, firstname, lastname, studentid, useremail):
    """
        Update the user's information in the database.

        Parameters:
            username (str): The user's username.
            firstname (str): The user's first name.
            lastname (str): The user's last name.
            studentid (str): The user's student ID.
            useremail (str): The user's email address.

        Raises:
            sqlite3.Error: If there is a database error during the update.
        """
    try:
        conn = sqlite3.connect('Comp2005.db')
        cursor = conn.cursor()
        update_query = "UPDATE UserProfile SET FirstName = ?, LastName = ?, StudentID = ?, UserEmail=?  WHERE " \
                       "UserName = ? "
        cursor.execute(update_query, (firstname, lastname, studentid, useremail, username))
        conn.commit()
        conn.close()
    except sqlite3.Error as e:
        print(f"SQLite error: {e}")
        raise e


if __name__ == '__main__':
    run(app=session_app, host='localhost', port=8080, debug=True)
