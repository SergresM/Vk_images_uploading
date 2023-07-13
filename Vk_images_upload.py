import os
import threading
import tkinter as tk
from tkinter import filedialog, ttk
from tkinter import messagebox
import vk_api
from vk_api import VkUpload
from vk_api.utils import get_random_id
import webbrowser

TOKEN_FILE = "token.txt"

def open_vkhost():
    webbrowser.open("https://vkhost.github.io")

def load_access_token():
    if os.path.isfile(TOKEN_FILE):
        with open(TOKEN_FILE, "r") as file:
            return file.read().strip()
    else:
        return None

def save_access_token(access_token):
    with open(TOKEN_FILE, "w") as file:
        file.write(access_token)

def auth_with_token():
    access_token = token_entry.get()

    vk_session = vk_api.VkApi(token=access_token)
    vk = vk_session.get_api()
    try:
        vk.users.get()
        save_access_token(access_token)
        messagebox.showinfo("Success", "Authorization successful!")
        print("Authorization successful!")  # Вывод лога
    except vk_api.exceptions.ApiError:
        messagebox.showerror("Error", "Invalid access token!")
        print("Invalid access token!")  # Вывод лога

def select_folder():
    root = tk.Tk()
    root.withdraw()
    folder_path = filedialog.askdirectory()
    return folder_path

chat_ids = {}

def select_chat():
    chat_title = chat_combobox.get()
    chat_id = chat_ids.get(chat_title)  # Получение идентификатора из словаря
    print(chat_id)
    if chat_id is None:
        messagebox.showerror("Error", "Invalid chat ID. Please select a chat.")
    return chat_id

def send_images_to_chat(access_token, folder_path, chat_id):
    vk_session = vk_api.VkApi(token=access_token)
    vk = vk_session.get_api()
    vk.users.get()
    save_access_token(access_token)

    upload = VkUpload(vk_session)

    def send_images_recursive(folder_path, chat_id):
        image_paths = []  # Список путей к изображениям

        for item in os.listdir(folder_path):
            item_path = os.path.join(folder_path, item)
            if os.path.isdir(item_path):
                send_images_recursive(item_path, chat_id)  # Рекурсивный вызов для вложенных папок
            else:
                # Проверка, что файл является изображением (можно добавить дополнительные проверки)
                if item_path.endswith('.jpg') or item_path.endswith('.png'):
                    image_paths.append(item_path)  # Добавление пути к изображению в список

        # Разделение списка изображений на группы по 10
        image_groups = [image_paths[i:i + 10] for i in range(0, len(image_paths), 10)]

        # Создание экземпляра VkUpload перед циклом
        upload = VkUpload(vk_session)

        # Отправка сообщений с группами изображений
        for group in image_groups:
            attachments = []
            for image_path in group:
                try:
                    # Загрузка изображения на сервер VK
                    photo_list = upload.photo_messages(image_path)
                    attachments.append(
                        f'photo{photo_list[0]["owner_id"]}_{photo_list[0]["id"]}_{photo_list[0]["access_key"]}')
                except vk_api.exceptions.ApiError as e:
                    print(f"Failed to upload image: {image_path}")
                    print(f"Error message: {e}")
                    continue

            # Отправка сообщения с группой изображений в беседу
            vk.messages.send(
                peer_id=chat_id,
                random_id=get_random_id(),
                attachment=','.join(attachments)
            )

        messagebox.showinfo("Success", "Images sent successfully!")

        print("Images sent successfully!")  # Вывод лога

    send_thread = threading.Thread(target=send_images_recursive, args=(folder_path, chat_id))
    send_thread.start()
    print("Sending images...")  # Вывод лога

root = tk.Tk()
root.title("Image Sender")
root.resizable(False, False)

window_width = 360
window_height = 300

screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

x = (screen_width // 2) - (window_width // 2)
y = (screen_height // 2) - (window_height // 2)

root.geometry(f"{window_width}x{window_height}+{x}+{y}")

def paste_from_clipboard():
    clipboard_text = root.clipboard_get()
    token_entry.delete(0, tk.END)
    token_entry.insert(0, clipboard_text.strip())

def paste_from_clipboard():
    clipboard_text = root.clipboard_get()
    token_entry.delete(0, tk.END)  # Очистка текстового поля
    token_entry.insert(0, get_access_token_from_string(clipboard_text.strip()))  # Вставка текста

def get_access_token_from_string(string):
    start_index = string.find('access_token=')
    end_index = string.find('&expires_in')
    if start_index != -1 and end_index != -1:
        return string[start_index + len('access_token='):end_index]
    else:
        return ""

def update_conversations():
    access_token = token_entry.get()

    vk_session = vk_api.VkApi(token=access_token)
    vk = vk_session.get_api()
    try:
        vk.users.get()
        save_access_token(access_token)
        messagebox.showinfo("Success", "Authorization successful!")
        conversations = vk.messages.getConversations(filter='all')['items']

        chat_list = []
        for item in conversations:
            chat_id = item["conversation"]["peer"]["id"]
            chat_settings = item["conversation"].get("chat_settings")
            if chat_settings is not None:
                chat_title = chat_settings.get("title")
                chat_list.append((chat_id, chat_title))
                chat_ids[chat_title] = chat_id  # Добавление значения в словарь
            else:
                chat_list.append((chat_id, None))

        chat_combobox["values"] = [conversation['conversation'].get('chat_settings', {}).get('title') for conversation in conversations]
        chat_combobox.current(0)  # Установка первого значения по умолчанию

    except vk_api.exceptions.ApiError:
        messagebox.showerror("Error", "Invalid access token!")


# Метка и поле для ввода токена
token_label = tk.Label(root, text="Access Token:")
token_label.grid(row=0, column=0, sticky="w", padx=10, pady=10)
token_entry = tk.Entry(root)
token_entry.grid(row=0, column=1, sticky="ew", padx=10, pady=10)

# Кнопка для вставки текста из буфера обмена
paste_button = tk.Button(root, text="Paste", command=paste_from_clipboard)
paste_button.grid(row=0, column=2, sticky='w')

# Кнопка для открытия веб-сайта VKHost
vkhost_button = tk.Button(root, text="Open VKHost", command=open_vkhost)
vkhost_button.grid(row=1, column=1, sticky="ew", padx=10, pady=10)

# Кнопка для авторизации
auth_button = tk.Button(root, text="Authorize", command=auth_with_token)
auth_button.grid(row=2, column=1, sticky="ew", padx=10, pady=10)

# Метка и кнопка для выбора папки
folder_label = tk.Label(root, text="Select Folder:")
folder_label.grid(row=3, column=0, sticky="w", padx=10, pady=10)
folder_button = tk.Button(root, text="Select", command=select_folder)
folder_button.grid(row=3, column=1, sticky="ew", padx=10, pady=10)

# Метка и кнопка для выбора беседы
chat_label = tk.Label(root, text="Select Chat:")
chat_label.grid(row=4, column=0, padx=10, pady=10)

# Создание графического интерфейса для выбора беседы
chat_frame = tk.Frame(root)
chat_frame.grid(row=4, column=1, sticky="ew", padx=10)

conversations = []

update_button = tk.Button(chat_frame, text="Update Conversations", command=update_conversations)
update_button.grid(row=0, column=0, pady=10, sticky="ew")


chat_combobox = ttk.Combobox(chat_frame, state="readonly")
chat_combobox.grid(row=1, column=0, padx=10, pady=5)

# Кнопка для отправки изображений в беседу
send_button = tk.Button(root, text="Send Images", command=lambda: send_images_to_chat(load_access_token(), select_folder(), select_chat()))
send_button.grid(row=5, column=1, pady=10)

root.mainloop()



