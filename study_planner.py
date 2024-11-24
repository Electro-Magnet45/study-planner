from colorama import Fore, init, Style as ColorStyle
from getpass import getpass
import mysql.connector
from mysql.connector import Error
from datetime import datetime
from tabulate import tabulate


init(autoreset=True)


def cinput(c1, p, c2):
    print(c1 + p, end="")
    value = input(c2).strip()
    return value


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
            print(Fore.RED + f"Error: {e}")
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
            print(Fore.RED + f"Error while initializing the database: {e}")
        finally:
            cursor.close()

    def register_user(self):
        print(ColorStyle.BRIGHT + Fore.MAGENTA + "\n---------- Register ----------")
        username = cinput(Fore.MAGENTA, "Enter a username: ", Fore.CYAN)
        password = getpass(Fore.MAGENTA + "Enter a password: ").strip()
        re_password = getpass(Fore.MAGENTA + "Re-enter your password: ").strip()

        if password != re_password:
            print(Fore.RED + "Passwords do not match!")
            return False

        cursor = self.db_connection.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (username, password) VALUES (%s, %s)",
                (username, password),
            )
            self.db_connection.commit()
            print(Fore.GREEN + "Registration successful!")
        except Error as e:
            print(Fore.RED + f"Error: {e}")
        finally:
            cursor.close()

    def login(self):
        print(Fore.MAGENTA + "\n---------- Login ----------")
        username = cinput(Fore.MAGENTA, "Enter your username: ", Fore.CYAN)
        password = getpass(Fore.MAGENTA + "Enter your password: ").strip()

        cursor = self.db_connection.cursor()
        try:
            cursor.execute(
                "SELECT id FROM users WHERE username = %s AND password = %s",
                (username, password),
            )
            user = cursor.fetchone()
            if user:
                self.current_user_id = user[0]
                print(Fore.GREEN + "Login successful!")
                return True
            else:
                print(Fore.RED + "Invalid credentials.")
                return False
        finally:
            cursor.close()

    def schedule_task(self):
        print(
            ColorStyle.BRIGHT + Fore.MAGENTA + "\n---------- Schedule a Task ----------"
        )

        subject = cinput(Fore.MAGENTA, "Enter the subject: ", Fore.CYAN).strip()
        title = cinput(Fore.MAGENTA, "Enter the title of the task: ", Fore.CYAN).strip()
        hours = cinput(
            Fore.MAGENTA, "Enter the number of hours to study: ", Fore.CYAN
        ).strip()

        while not hours.isdigit():
            print(Fore.RED + "Please enter a valid number of hours.")
            hours = input(Fore.CYAN + "Enter the number of hours to study: ").strip()

        hours = int(hours)
        due_date = cinput(
            Fore.MAGENTA, "Enter the due date (YYYY-MM-DD): ", Fore.CYAN
        ).strip()

        try:
            due_date_obj = datetime.strptime(due_date, "%Y-%m-%d")
        except ValueError:
            print(
                Fore.RED
                + "Invalid date format. Please enter the date in YYYY-MM-DD format."
            )
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
            print(Fore.GREEN + "Task scheduled successfully!")
        except Error as e:
            print(Fore.RED + f"Error while scheduling task: {e}")
        finally:
            cursor.close()

    def edit_task(self):
        print(Fore.MAGENTA + "\n---------- Edit Task ----------")
        cursor = self.db_connection.cursor(dictionary=True)

        task_id = cinput(
            Fore.MAGENTA, "\nEnter the ID of the task you want to edit: ", Fore.CYAN
        ).strip()

        cursor.execute(
            "SELECT * FROM tasks WHERE id = %s AND user_id = %s",
            (task_id, self.current_user_id),
        )
        task = cursor.fetchone()

        if not task:
            print(Fore.RED + "Invalid task ID.")
            cursor.close()
            return

        status_value = 0 if task["status"] == "pending" else 1
        subject = (
            cinput(
                Fore.MAGENTA,
                f"Enter new subject (current: {task['subject']}): ",
                Fore.CYAN,
            ).strip()
            or task["subject"]
        )
        title = (
            cinput(
                Fore.MAGENTA,
                f"Enter new title (current: {task['title']}): ",
                Fore.CYAN,
            ).strip()
            or task["title"]
        )
        hours = (
            cinput(
                Fore.MAGENTA,
                f"Enter new study hours (current: {task['hours']}): ",
                Fore.CYAN,
            ).strip()
            or task["hours"]
        )
        due_date = (
            cinput(
                Fore.MAGENTA,
                f"Enter new due date (current: {task['due_date']}): ",
                Fore.CYAN,
            ).strip()
            or task["due_date"]
        )
        status = (
            cinput(
                Fore.MAGENTA,
                f"Enter new status (current: {'Completed' if task['status'] == 1 else 'Pending'}): ",
                Fore.CYAN,
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
            print(Fore.GREEN + "Task updated successfully!")
        except Error as e:
            print(Fore.RED + f"Error updating task: {e}")
        finally:
            cursor.close()

    def delete_task(self):
        print(Fore.MAGENTA + "\n---------- Delete Task ----------")

        cursor = self.db_connection.cursor(dictionary=True)
        task_id = cinput(
            Fore.MAGENTA, "\nEnter the ID of the task you want to delete: ", Fore.CYAN
        ).strip()

        cursor.execute(
            "SELECT * FROM tasks WHERE id = %s AND user_id = %s",
            (task_id, self.current_user_id),
        )
        task = cursor.fetchone()

        if not task:
            print(Fore.RED + "Invalid task ID.")
            cursor.close()
            return

        confirm = (
            cinput(
                Fore.MAGENTA,
                f"Are you sure you want to delete the task '{task['title']}'? (y/n): ",
                Fore.CYAN,
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
                print(Fore.GREEN + "Task deleted successfully!")
            except Error as e:
                print(Fore.RED + f"Error deleting task: {e}")
        else:
            print(Fore.YELLOW + "Task deletion canceled.")

        cursor.close()

    def view_tasks(self):
        print(Fore.MAGENTA + "\n---------- View Tasks ----------")
        cursor = self.db_connection.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT id, subject, title, hours, due_date, status FROM tasks WHERE user_id = %s",
                (self.current_user_id,),
            )

            tasks = cursor.fetchall()
            if not tasks:
                print(Fore.YELLOW + "You have no tasks scheduled.\n")
                return

            choice = (
                cinput(
                    Fore.MAGENTA,
                    "Do you want to view tasks in tabular or detailed format ? (t/d): ",
                    Fore.CYAN,
                )
                .strip()
                .lower()
            ) or "t"

            if choice == "t":
                table_data = [
                    [
                        task["id"],
                        task["subject"],
                        task["title"],
                        f"{task['hours']} hours",
                        task["due_date"],
                        "Completed" if task["status"] == 1 else "Pending",
                    ]
                    for task in tasks
                ]
                headers = ["Task ID", "Subject", "Title", "Hours", "Due Date", "Status"]
                print(
                    Fore.CYAN
                    + tabulate(table_data, headers=headers, tablefmt="fancy_grid")
                )
            else:
                print(Fore.CYAN + "Here are your scheduled tasks:\n")
                print(Fore.GREEN + "===========================================")

                for task in tasks:
                    print(Fore.YELLOW + f"Task ID: {task['id']}")
                    print(Fore.CYAN + f"Subject  : {task['subject']}")
                    print(Fore.CYAN + f"Title    : {task['title']}")
                    print(Fore.CYAN + f"Hours    : {task['hours']} hours")
                    print(Fore.CYAN + f"Due Date : {task['due_date']}")
                    print(
                        Fore.CYAN
                        + f"Status : {'Completed' if task['status'] == 1 else 'Pending'}"
                    )
                    print(Fore.GREEN + "-------------------------------------------")

        except Error as e:
            print(Fore.RED + f"Error retrieving tasks: {e}")
        finally:
            cursor.close()

    def generate_report(self):
        print(Fore.MAGENTA + "\n---------- Generate Report ----------")
        cursor = self.db_connection.cursor(dictionary=True)

        filter_choice = (
            cinput(
                Fore.MAGENTA,
                "Do you want to filter the report by subject, status, date, or none? (subject/status/date/none): ",
                Fore.CYAN,
            )
            .strip()
            .lower()
        )

        if filter_choice == "subject":
            subject_filter = cinput(
                Fore.MAGENTA, "Enter the subject to filter by: ", Fore.CYAN
            ).strip()
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
                cinput(
                    Fore.MAGENTA,
                    "Enter the status to filter by (completed/pending): ",
                    Fore.CYAN,
                )
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

        result = cursor.fetchall()

        if not result:
            print(Fore.YELLOW + "No data found for the selected filter.")
            cursor.close()
            return

        if filter_choice == "date":
            table_data = [
                [
                    record["due_date"],
                    record["completed_tasks"],
                    record["pending_tasks"],
                ]
                for record in result
            ]
            headers = ["Due Date", "Completed Tasks", "Pending Tasks"]
        else:
            table_data = [
                [
                    entry["subject"],
                    entry["total_hours"],
                    entry["task_count"],
                    entry["completed_tasks"],
                    entry["pending_tasks"],
                ]
                for entry in result
            ]
            headers = ["Subject", "Total Hours", "Total Tasks", "Completed", "Pending"]

        print(Fore.CYAN + tabulate(table_data, headers=headers, tablefmt="fancy_grid"))
        cursor.close()

    def edit_account(self):
        print(Fore.MAGENTA + "\n---------- Edit Account ----------")
        cursor = self.db_connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT username FROM users WHERE id = %s", (self.current_user_id,)
        )
        user = cursor.fetchone()
        current_username = user["username"]
        print(Fore.CYAN + f"Current Username: {current_username}")

        change_username = (
            cinput(
                Fore.MAGENTA,
                "Do you want to change your username? (y/n): ",
                Fore.CYAN,
            )
            .strip()
            .lower()
        )

        if change_username == "y":
            new_username = cinput(
                Fore.MAGENTA, "Enter a new username: ", Fore.CYAN
            ).strip()
            cursor.execute("SELECT id FROM users WHERE username = %s", (new_username,))
            if cursor.fetchone():
                print(Fore.RED + "Username already taken, please choose another.")
                cursor.close()
                return

            cursor.execute(
                "UPDATE users SET username = %s WHERE id = %s",
                (new_username, self.current_user_id),
            )
            self.db_connection.commit()
            print(Fore.GREEN + "Username updated successfully!")

        change_password = (
            cinput(
                Fore.MAGENTA,
                "Do you want to change your password? (y/n): ",
                Fore.CYAN,
            )
            .strip()
            .lower()
        )

        if change_password == "y":
            password = getpass(Fore.MAGENTA + "Enter a new password: ").strip()
            re_password = getpass(Fore.MAGENTA + "Re-enter your new password: ").strip()

            if password != re_password:
                print(Fore.RED + "Passwords do not match!")
                cursor.close()
                return

            cursor.execute(
                "UPDATE users SET password = %s WHERE id = %s",
                (password, self.current_user_id),
            )
            self.db_connection.commit()
            print(Fore.GREEN + "Password updated successfully!")

        cursor.close()

    def main_menu(self):
        while True:
            print(
                ColorStyle.BRIGHT
                + Fore.BLUE
                + "\n================ Main Menu ================"
            )
            if self.current_user_id:
                cursor = self.db_connection.cursor(dictionary=True)
                cursor.execute(
                    "SELECT username FROM users WHERE id = %s", (self.current_user_id,)
                )
                user = cursor.fetchone()
                username = user["username"] if user else "User"
                cursor.close()
                print(Fore.GREEN + f"Welcome, {username}!")
                print(Fore.YELLOW + "\nChoose an option from the menu below:")
                print(Fore.CYAN + "1. Schedule a Task")
                print(Fore.CYAN + "2. Edit a Task")
                print(Fore.CYAN + "3. Delete a Task")
                print(Fore.CYAN + "4. View Tasks")
                print(Fore.CYAN + "5. Generate Report")
                print(Fore.CYAN + "6. Edit Account")
                print(Fore.CYAN + "7. Logout")
                print(Fore.CYAN + "8. Exit")
                choice = cinput(
                    Fore.CYAN + ColorStyle.BRIGHT, "Enter your choice: ", Fore.GREEN
                )

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
                    self.edit_account()
                elif choice == "7":
                    print(Fore.GREEN + "Logging out...")
                    self.current_user_id = None
                elif choice == "8":
                    print(Fore.GREEN + "Exiting the application. Goodbye!")
                    break
                else:
                    print(Fore.RED + "Feature not implemented yet!")

            else:
                print(Fore.YELLOW + "\nPlease choose an option to proceed:")
                print(Fore.CYAN + "1. Register")
                print(Fore.CYAN + "2. Login")
                print(Fore.CYAN + "3. Exit")
                choice = cinput(
                    Fore.CYAN + ColorStyle.BRIGHT, "Enter your choice: ", Fore.GREEN
                )

                if choice == "1":
                    self.register_user()
                elif choice == "2":
                    if self.login():
                        continue
                elif choice == "3":
                    print(Fore.GREEN + "Exiting the application. Goodbye!")
                    break
                else:
                    print(Fore.RED + "Invalid choice. Please try again.")


if __name__ == "__main__":
    planner = StudyPlanner()
    planner.main_menu()
