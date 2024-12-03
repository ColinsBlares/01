import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
from tkinter.simpledialog import askstring
import mysql.connector


# Функция подключения к базе данных MySQL
def connect_db():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="test"
        )
        return connection
    except mysql.connector.Error as err:
        messagebox.showerror("Error", f"Ошибка подключения: {err}")
        return None


# Функция регистрации пользователя
def register_user():
    username = entry_username.get()
    password = entry_password.get()

    if not username or not password:
        messagebox.showwarning("Input Error", "Пожалуйста, введите имя пользователя и пароль.")
        return

    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user:
            messagebox.showwarning("Username Taken", "Это имя пользователя уже занято.")
        else:
            cursor.execute("INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                           (username, password, 'user'))
            connection.commit()
            messagebox.showinfo("Success", "Регистрация прошла успешно.")

        connection.close()


# Функция авторизации пользователя
def login_user(event=None):  # Добавлен параметр event для поддержки события клавиши
    username = entry_username.get()
    password = entry_password.get()

    if not username or not password:
        messagebox.showwarning("Input Error", "Пожалуйста, введите имя пользователя и пароль.")
        return

    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, password))
        user = cursor.fetchone()

        if user:
            role = user[3]  # Извлекаем роль из результата запроса
            messagebox.showinfo("Login Successful", f"Добро пожаловать, {username}! Ваша роль: {role}")
            open_table_window(role)  # Передаем роль в окно с таблицей
        else:
            messagebox.showerror("Login Failed", "Неверное имя пользователя или пароль.")

        connection.close()


# Функция для изменения роли пользователя
def change_role(user_id):
    # Запрашиваем новую роль
    new_role = askstring("Изменить роль", "Введите новую роль (user/admin/moderator):")

    if new_role:
        if new_role not in ['user', 'admin', 'moderator']:  # Проверка на допустимые роли
            messagebox.showwarning("Invalid Role", "Роль должна быть одной из: user, admin, moderator.")
            return

        connection = connect_db()
        if connection:
            cursor = connection.cursor()
            cursor.execute("UPDATE users SET role = %s WHERE id = %s", (new_role, user_id))
            connection.commit()
            messagebox.showinfo("Success", "Роль успешно изменена.")
            update_table()  # Обновляем таблицу после изменения роли
            connection.close()


# Функция для удаления записи
def delete_record(user_id):
    confirm = messagebox.askyesno("Удаление записи", "Вы уверены, что хотите удалить этого пользователя?")
    if confirm:
        connection = connect_db()
        if connection:
            cursor = connection.cursor()
            cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
            connection.commit()
            messagebox.showinfo("Success", "Пользователь удален.")
            update_table()  # Обновляем таблицу после удаления записи
            connection.close()


# Окно с таблицей для просмотра данных
def open_table_window(role):
    global tree  # Сделаем tree глобальной переменной

    table_window = tk.Toplevel(root)  # Создаем новое окно поверх главного
    table_window.title("Таблица пользователей")

    # Создаем таблицу с использованием Treeview
    tree = ttk.Treeview(table_window, columns=("ID", "Username", "Password", "Role"), show="headings")

    tree.heading("ID", text="ID")
    tree.heading("Username", text="Имя пользователя")
    tree.heading("Password", text="Пароль пользователя")
    tree.heading("Role", text="Роль")

    # Добавляем кнопку для изменения роли и удаления записи (только для админа)
    def on_role_change(event):
        if role == 'moderator' or role == "user":
            messagebox.showwarning("Permission Denied", "Модератор не может изменять роли.")
            return

        selected_item = tree.selection()
        if selected_item:
            user_id = tree.item(selected_item)["values"][0]  # Получаем ID выбранного пользователя
            change_role(user_id)

    def on_delete(event):
        if role == 'moderator':
            messagebox.showwarning("Permission Denied", "Модератор не может удалять записи.")
            return

        selected_item = tree.selection()
        if selected_item:
            user_id = tree.item(selected_item)["values"][0]  # Получаем ID выбранного пользователя
            delete_record(user_id)

    tree.bind("<Double-1>", on_role_change)  # Связываем двойной клик с изменением роли
    tree.bind("<Delete>", on_delete)  # Связываем клавишу Delete с удалением записи

    # Получаем данные из базы данных
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()

        # Заполняем таблицу данными
        for row in rows:
            tree.insert("", "end", values=row)

        connection.close()

    tree.pack(padx=10, pady=10, expand=True, fill=tk.BOTH)

    # Для модераторов скрываем элементы управления
    if role == 'moderator':
        # Для модератора скрываем кнопки изменения роли и удаления
        tree.bind("<Delete>", lambda e: None)  # Отключаем удаление для модераторов


# Функция обновления таблицы после изменения роли
def update_table():
    # Получаем данные из базы данных и обновляем таблицу
    connection = connect_db()
    if connection:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()

        # Очищаем таблицу перед обновлением
        for item in tree.get_children():
            tree.delete(item)

        # Заполняем таблицу новыми данными
        for row in rows:
            tree.insert("", "end", values=row)

        connection.close()


# Создание окна Tkinter
root = tk.Tk()
root.title("Авторизация и Регистрация")

# Поля для ввода
label_username = tk.Label(root, text="Имя пользователя:")
label_username.grid(row=0, column=0, padx=10, pady=10)
entry_username = tk.Entry(root)
entry_username.grid(row=0, column=1, padx=10, pady=10)

label_password = tk.Label(root, text="Пароль:")
label_password.grid(row=1, column=0, padx=10, pady=10)
entry_password = tk.Entry(root, show="*")
entry_password.grid(row=1, column=1, padx=10, pady=10)

# Кнопки регистрации и авторизации
button_register = tk.Button(root, text="Зарегистрироваться", command=register_user)
button_register.grid(row=2, column=0, padx=10, pady=10)

button_login = tk.Button(root, text="Войти", command=login_user)
button_login.grid(row=2, column=1, padx=10, pady=10)

# Привязка клавиши Enter к функции login_user
root.bind("<Return>", login_user)  # Связываем нажатие клавиши Enter с функцией входа

# Запуск окна
root.mainloop()
