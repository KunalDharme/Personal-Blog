import os
import shutil
from datetime import datetime

def backup_file(src, dest_folder):
    if not os.path.exists(src):
        print(f"No file or folder found at {src} to backup.")
        return False
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    base_name = os.path.basename(src)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f"{base_name}_backup_{timestamp}"
    dest = os.path.join(dest_folder, backup_name)
    if os.path.isfile(src):
        shutil.copy2(src, dest)
    else:
        shutil.copytree(src, dest)
    print(f"Backup of '{src}' created at '{dest}'.")
    return True

def reset_database():
    print("Starting database and uploads reset process.")

    backup_choice = input("Do you want to backup current database and uploads before deleting? (yes/no): ").strip().lower()

    if backup_choice == 'yes':
        print("Backing up database and uploads...")
        backup_dir = "backups"
        backup_file("instance/blog.db", backup_dir)
        backup_file("static/uploads", backup_dir)
    else:
        print("Skipping backup...")

    # Remove database file
    db_path = "instance/blog.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        print("Deleted database file: instance/blog.db")
    else:
        print("Database file not found, skipping deletion.")

    # Remove all files inside uploads folder
    uploads_path = "static/uploads"
    if os.path.exists(uploads_path):
        for filename in os.listdir(uploads_path):
            file_path = os.path.join(uploads_path, filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(f"Failed to delete {file_path}. Reason: {e}")
        print("Cleared all files inside static/uploads/")
    else:
        print("Uploads folder not found, skipping deletion.")

    print("Creating fresh database and tables...")
    os.system("python create_db.py")

    print("Creating admin user...")
    from app import app
    from admin.models import create_admin

    with app.app_context():
        create_admin()

    print("\nReset complete! You can now start the app with:")
    print("python app.py")
    print("Access your site at http://127.0.0.1:5000 and admin at http://127.0.0.1:5000/admin")

if __name__ == "__main__":
    reset_database()
