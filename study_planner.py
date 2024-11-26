import mysql.connector
from mysql.connector import Error
from datetime import datetime


class StudyPlanner:
    def __init__(self):
        self.db_connection = self.connect_db()
        self.current_user_id = None
        self.initialize_database()

    def connect_db(self):
        try:
            connection = mysql.connector.connect(
                host="localhost",
                user="root",
                password="mysql",
            )
            return connection
        except Error as e:
            print(f"Error: {e}")
            return None

    def initialize_database(self):
        try:
            cursor = self.db_connection.cursor()
            cursor.execute("CREATE DATABASE IF NOT EXISTS study_planner")
            cursor.execute("USE study_planner")

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL
                )
            """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS tasks (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    subject VARCHAR(100),
                    title VARCHAR(50),
                    hours INT,
                    due_date DATE,
                    status INT DEFAULT 0,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """
            )
        except Error as e:
            print(f"Error while initializing the database: {e}")
        finally:
            cursor.close()

    def register_user(self):
        print("\n---------- Register ----------")
        username = input("Enter a username: ")
        password = input("Enter a password: ").strip()
        re_password = input("Re-enter your password: ").strip()

        if password != re_password:
            print("Passwords do not match!")
            return False

        cursor = self.db_connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, password),
            )
            self.db_connection.commit()
            print("Registration successful!")
        except Error as e:
            print(f"Error: {e}")
        finally:
            cursor.close()

    def login(self):
        print("\n---------- Login ----------")
        username = input("Enter your username: ")
        password = input("Enter your password: ").strip()

        cursor = self.db_connection.cursor()
        try:
            cursor.execute(
                "SELECT id FROM users WHERE username = %s AND password = %s",
                (username, password),
            )
            user = cursor.fetchone()
            if user:
                self.current_user_id = user[0]
                print("Login successful!")
                return True
            else:
                print("Invalid credentials.")
                return False
        finally:
            cursor.close()

    def schedule_task(self):
        print("\n---------- Schedule a Task ----------")

        subject = input("Enter the subject: ").strip()
        title = input("Enter the title of the task: ").strip()
        hours = input("Enter the number of hours to study: ").strip()

        while not hours.isdigit():
            print("Please enter a valid number of hours.")
            hours = input("Enter the number of hours to study: ").strip()

        hours = int(hours)
        due_date = input("Enter the due date (YYYY-MM-DD): ").strip()

        try:
            due_date_obj = datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            print("Invalid date format. Please enter the date in YYYY-MM-DD format.")
            return

        cursor = self.db_connection.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO tasks (user_id, subject, title, hours, due_date, status)
                VALUES (%s, %s, %s, %s, %s, 0)
                """,
                (self.current_user_id, subject, title, hours, due_date_obj),
            )
            self.db_connection.commit()
            print("Task scheduled successfully!")
        except Error as e:
            print(f"Error while scheduling task: {e}")
        finally:
            cursor.close()

    def edit_task(self):
        print("\n---------- Edit Task ----------")
        cursor = self.db_connection.cursor(dictionary=True)

        task_id = input("\nEnter the ID of the task you want to edit: ").strip()

        cursor.execute(
            "SELECT * FROM tasks WHERE id = %s AND user_id = %s",
            (task_id, self.current_user_id),
        )
        task = cursor.fetchone()

        if not task:
            print("Invalid task ID.")
            cursor.close()
            return

        status_value = 0 if task["status"] == "pending" else 1
        subject = (
            input(f"Enter new subject (current: {task['subject']}): ").strip()
            or task["subject"]
        )
        title = (
            input(f"Enter new title (current: {task['title']}): ").strip()
            or task["title"]
        )
        hours = (
            input(f"Enter new study hours (current: {task['hours']}): ").strip()
            or task["hours"]
        )
        due_date = (
            input(f"Enter new due date (current: {task['due_date']}): ").strip()
            or task["due_date"]
        )
        status = (
            input(
                f"Enter new status (current: {'Completed' if task['status'] == 1 else 'Pending'}): "
            )
            .strip()
            .lower()
            or status_value
        )
        status_value = 0 if status == "pending" else 1

        try:
            cursor.execute(
                """
                UPDATE tasks 
                SET subject = %s, title = %s, hours = %s, due_date = %s, status = %s
                WHERE id = %s AND user_id = %s
                """,
                (
                    subject,
                    title,
                    hours,
                    due_date,
                    status_value,
                    task_id,
                    self.current_user_id,
                ),
            )
            self.db_connection.commit()
            print("Task updated successfully!")
        except Error as e:
            print(f"Error updating task: {e}")
        finally:
            cursor.close()

    def delete_task(self):
        print("\n---------- Delete Task ----------")

        cursor = self.db_connection.cursor(dictionary=True)
        task_id = input("\nEnter the ID of the task you want to delete: ").strip()

        cursor.execute(
            "SELECT * FROM tasks WHERE id = %s AND user_id = %s",
            (task_id, self.current_user_id),
        )
        task = cursor.fetchone()

        if not task:
            print("Invalid task ID.")
            cursor.close()
            return

        confirm = (
            input(
                f"Are you sure you want to delete the task '{task['title']}'? (y/n): "
            )
            .strip()
            .lower()
        )

        if confirm == "y":
            try:
                cursor.execute(
                    "DELETE FROM tasks WHERE id = %s AND user_id = %s",
                    (task_id, self.current_user_id),
                )
                self.db_connection.commit()
                print("Task deleted successfully!")
            except Error as e:
                print(f"Error deleting task: {e}")
        else:
            print("Task deletion canceled.")

        cursor.close()

    def view_tasks(self):
        print("\n---------- View Tasks ----------")
        cursor = self.db_connection.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT id, subject, title, hours, due_date, status FROM tasks WHERE user_id = %s",
                (self.current_user_id,),
            )

            tasks = cursor.fetchall()
            if not tasks:
                print("You have no tasks scheduled.\n")
                return

            print("Here are your scheduled tasks:\n")
            print("===========================================")

            for task in tasks:
                print(f"\nTask ID: {task['id']}")
                print(f"Subject  : {task['subject']}")
                print(f"Title    : {task['title']}")
                print(f"Hours    : {task['hours']} hours")
                print(f"Due Date : {task['due_date']}")
                print(f"Status : {'Completed' if task['status'] == 1 else 'Pending'}")
                print("-------------------------------------------")

        except Error as e:
            print(f"Error retrieving tasks: {e}")
        finally:
            cursor.close()

    def generate_report(self):
        print("\n---------- Generate Report ----------")
        cursor = self.db_connection.cursor(dictionary=True)

        filter_choice = (
            input(
                "Do you want to filter the report by subject, status, date, or none? (subject/status/date/none): "
            )
            .strip()
            .lower()
        )

        if filter_choice == "subject":
            subject_filter = input("Enter the subject to filter by: ").strip()
            query = """
                    SELECT subject, SUM(hours) as total_hours, COUNT(*) as task_count, 
                        SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as completed_tasks,
                        SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) as pending_tasks
                    FROM tasks 
                    WHERE user_id = %s AND subject = %s
                    GROUP BY subject
                """
            cursor.execute(query, (self.current_user_id, subject_filter))

        elif filter_choice == "status":
            status_filter = (
                input("Enter the status to filter by (completed/pending): ")
                .strip()
                .lower()
            )
            status_value = 1 if status_filter == "completed" else 0
            query = """
                    SELECT subject, SUM(hours) as total_hours, COUNT(*) as task_count, 
                        SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as completed_tasks,
                        SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) as pending_tasks
                    FROM tasks 
                    WHERE user_id = %s AND status = %s
                    GROUP BY subject
                """
            cursor.execute(query, (self.current_user_id, status_value))

        elif filter_choice == "date":
            query = """
                SELECT
                    `due_date`,
                    SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as completed_tasks,
                    SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) as pending_tasks
                FROM tasks
                WHERE user_id = %s
                GROUP BY `due_date`
                ORDER BY `due_date`
            """
            cursor.execute(query, (self.current_user_id,))

        else:
            query = """
                    SELECT subject, SUM(hours) as total_hours, COUNT(*) as task_count, 
                        SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) as completed_tasks,
                        SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) as pending_tasks
                    FROM tasks 
                    WHERE user_id = %s
                    GROUP BY subject
                """
            cursor.execute(query, (self.current_user_id,))

        tasks = cursor.fetchall()

        if not tasks:
            print("No data found for the selected filter.")
            cursor.close()
            return

        if filter_choice == "date":
            for task in tasks:
                print(f"\nDue Date: {task['due_date']}")
                print(f"Completed Tasks  : {task['completed_tasks']}")
                print(f"Pending Tasks    : {task['pending_tasks']}")
                print("-------------------------------------------")
        else:
            for task in tasks:
                print(f"\nSubject  : {task['subject']}")
                print(f"Total Hours    : {task['total_hours']} hours")
                print(f"Task Count    : {task['task_count']}")
                print(f"Completed Tasks : {task['completed_tasks']}")
                print(f"Pending Tasks : {task['pending_tasks']}")
                print("-------------------------------------------")
        cursor.close()

    def view_summary(self):
        cursor = self.db_connection.cursor(dictionary=True)
        try:
            cursor.execute(
                """
                SELECT 
                    SUM(CASE WHEN status = 1 THEN 1 ELSE 0 END) AS completed,
                    SUM(CASE WHEN status = 0 THEN 1 ELSE 0 END) AS pending,
                    COUNT(*) AS total
                FROM tasks WHERE user_id = %s
                """,
                (self.current_user_id,),
            )
            result = cursor.fetchone()
            print(f"\nCompleted Tasks: {result['completed']}")
            print(f"Pending Tasks: {result['pending']}")
            print(f"Total Tasks: {result['total']}")
        except Error as e:
            print(f"Error fetching task summary: {e}")
        finally:
            cursor.close()

    def edit_account(self):
        print("\n---------- Edit Account ----------")
        cursor = self.db_connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT username FROM users WHERE id = %s", (self.current_user_id,)
        )
        user = cursor.fetchone()
        current_username = user["username"]
        print(f"Current Username: {current_username}")

        change_username = (
            input("Do you want to change your username? (y/n): ").strip().lower()
        )

        if change_username == "y":
            new_username = input("Enter a new username: ").strip()
            cursor.execute("SELECT id FROM users WHERE username = %s", (new_username,))
            if cursor.fetchone():
                print("Username already taken, please choose another.")
                cursor.close()
                return

            cursor.execute(
                "UPDATE users SET username = %s WHERE id = %s",
                (new_username, self.current_user_id),
            )
            self.db_connection.commit()
            print("Username updated successfully!")

        change_password = (
            input("Do you want to change your password? (y/n): ").strip().lower()
        )

        if change_password == "y":
            password = input("Enter a new password: ").strip()
            re_password = input("Re-enter your new password: ").strip()

            if password != re_password:
                print("Passwords do not match!")
                cursor.close()
                return

            cursor.execute(
                "UPDATE users SET password = %s WHERE id = %s",
                (password, self.current_user_id),
            )
            self.db_connection.commit()
            print("Password updated successfully!")

        cursor.close()

    def main_menu(self):
        while True:
            print("\n================ Main Menu ================")
            if self.current_user_id:
                cursor = self.db_connection.cursor(dictionary=True)
                cursor.execute(
                    "SELECT username FROM users WHERE id = %s", (self.current_user_id,)
                )
                user = cursor.fetchone()
                username = user["username"] if user else "User"
                cursor.close()

                print(f"Welcome, {username}!")
                print("\nChoose an option from the menu below:")
                print("1. Schedule a Task")
                print("2. Edit a Task")
                print("3. Delete a Task")
                print("4. View Tasks")
                print("5. Generate Report")
                print("6. View Summary")
                print("7. Edit Account")
                print("8. Logout")
                print("9. Exit")
                choice = input("Enter your choice: ")

                if choice == "1":
                    self.schedule_task()
                elif choice == "2":
                    self.edit_task()
                elif choice == "3":
                    self.delete_task()
                elif choice == "4":
                    self.view_tasks()
                elif choice == "5":
                    self.generate_report()
                elif choice == "6":
                    self.view_summary()
                elif choice == "7":
                    self.edit_account()
                elif choice == "8":
                    print("Logging out...")
                    self.current_user_id = None
                elif choice == "9":
                    print("Exiting the application. Goodbye!")
                    break
                else:
                    print("Feature not implemented yet!")

            else:
                print("\nPlease choose an option to proceed:")
                print("1. Register")
                print("2. Login")
                print("3. Exit")
                choice = input("Enter your choice: ")

                if choice == "1":
                    self.register_user()
                elif choice == "2":
                    if self.login():
                        continue
                elif choice == "3":
                    print("Exiting the application. Goodbye!")
                    break
                else:
                    print("Invalid choice. Please try again.")


if __name__ == "__main__":
    planner = StudyPlanner()
    planner.main_menu()
