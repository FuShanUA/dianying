import os
import sys
import json
import sqlite3
import requests
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Base Paths
APP_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = '/Users/shanfu/cc/.agents/skills/google-drive-sync/credentials.json'
TOKEN_PATH = '/Users/shanfu/cc/.agents/skills/google-drive-sync/token.json'
COVERS_DIR = os.path.join(APP_DIR, 'covers')
JSON_MAP_PATH = os.path.join(APP_DIR, 'covers_gdrive.json')

SCOPES = ['https://www.googleapis.com/auth/drive.file', 'https://www.googleapis.com/auth/drive']

def get_credentials():
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Token refresh failed: {e}")
                creds = None
                
        if not creds:
            if not os.path.exists(CREDENTIALS_PATH):
                print(f"Error: missing credentials.json at {CREDENTIALS_PATH}")
                sys.exit(1)
            
            print("Initiating Google Drive authentication flow. Please check your browser...")
            from google_auth_oauthlib.flow import InstalledAppFlow
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)
            
            with open(TOKEN_PATH, 'w') as token:
                token.write(creds.to_json())
    return creds

def get_drive_service():
    return build('drive', 'v3', credentials=get_credentials())

def get_or_create_covers_folder(service):
    # Search for folder named 'MovieLabelCovers'
    query = "name = 'MovieLabelCovers' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    results = service.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
    files = results.get('files', [])
    
    if files:
        folder_id = files[0]['id']
        print(f"Found existing Google Drive folder 'MovieLabelCovers' with ID: {folder_id}")
        return folder_id
        
    # Create new folder
    print("Creating new Google Drive folder 'MovieLabelCovers'...")
    file_metadata = {
        'name': 'MovieLabelCovers',
        'mimeType': 'application/vnd.google-apps.folder'
    }
    folder = service.files().create(body=file_metadata, fields='id').execute()
    folder_id = folder.get('id')
    
    # Make the folder publicly readable ("Anyone with the link can view")
    print("Setting folder permission to 'anyone with the link can view'...")
    service.permissions().create(
        fileId=folder_id,
        body={
            'role': 'reader',
            'type': 'anyone'
        }
    ).execute()
    
    print(f"Google Drive folder created and shared publicly! ID: {folder_id}")
    return folder_id

def load_gdrive_mapping():
    if os.path.exists(JSON_MAP_PATH):
        try:
            with open(JSON_MAP_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_gdrive_mapping(mapping):
    with open(JSON_MAP_PATH, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, indent=4, ensure_ascii=False)

def get_remote_files_in_folder(service, folder_id):
    query = f"'{folder_id}' in parents and trashed = false"
    remote_files = {}
    page_token = None
    
    print("Listing existing files in Google Drive folder...")
    while True:
        results = service.files().list(
            q=query,
            spaces='drive',
            fields='nextPageToken, files(id, name)',
            pageToken=page_token,
            pageSize=1000
        ).execute()
        
        for f in results.get('files', []):
            remote_files[f['name']] = f['id']
            
        page_token = results.get('nextPageToken')
        if not page_token:
            break
            
    print(f"Found {len(remote_files)} existing files in remote folder.")
    return remote_files

def main():
    creds = get_credentials()
    service = build('drive', 'v3', credentials=creds)
    folder_id = get_or_create_covers_folder(service)
    
    mapping = load_gdrive_mapping()
    remote_files = get_remote_files_in_folder(service, folder_id)
    
    # Identify local files
    if not os.path.exists(COVERS_DIR):
        print(f"Error: covers directory not found at {COVERS_DIR}")
        sys.exit(1)
        
    local_files = [f for f in os.listdir(COVERS_DIR) if f.endswith('.jpg')]
    total_local = len(local_files)
    print(f"Found {total_local} local cover images.")
    
    to_upload = []
    skipped_count = 0
    saved_counter = 0
    
    for filename in local_files:
        movie_id_str = filename.replace('.jpg', '')
        if filename in remote_files:
            file_id = remote_files[filename]
            if mapping.get(movie_id_str) != file_id:
                mapping[movie_id_str] = file_id
                saved_counter += 1
            skipped_count += 1
        else:
            to_upload.append(filename)
            
    if saved_counter > 0:
        save_gdrive_mapping(mapping)
        
    print(f"Skipped {skipped_count} files. {len(to_upload)} files to upload.")
    
    if not to_upload:
        print("Everything is up to date!")
        return

    thread_local = threading.local()

    def get_thread_service():
        if not hasattr(thread_local, "service"):
            thread_local.service = build('drive', 'v3', credentials=creds)
        return thread_local.service

    def upload_worker(filename):
        local_path = os.path.join(COVERS_DIR, filename)
        movie_id_str = filename.replace('.jpg', '')
        
        file_metadata = {
            'name': filename,
            'parents': [folder_id]
        }
        media = MediaFileUpload(local_path, mimetype='image/jpeg', resumable=True)
        
        local_svc = get_thread_service()
        uploaded_file = local_svc.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        file_id = uploaded_file.get('id')
        
        # Make each file individually public (folder permission is NOT inherited)
        local_svc.permissions().create(
            fileId=file_id,
            body={'role': 'reader', 'type': 'anyone'}
        ).execute()
        
        return filename, movie_id_str, file_id

    uploaded_count = 0
    saved_counter = 0
    
    print("Starting multi-threaded upload (15 workers)...")
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(upload_worker, fname): fname for fname in to_upload}
        
        for future in as_completed(futures):
            fname = futures[future]
            try:
                filename, movie_id_str, file_id = future.result()
                mapping[movie_id_str] = file_id
                uploaded_count += 1
                saved_counter += 1
                
                print(f"[{uploaded_count}/{len(to_upload)}] Uploaded {filename}")
                
                if saved_counter >= 50:
                    save_gdrive_mapping(mapping)
                    saved_counter = 0
                    
            except Exception as e:
                print(f"Failed to upload {fname}: {e}")
                
    # Final save
    save_gdrive_mapping(mapping)
    print("\nSync completed successfully!")
    print(f"Total processed: {total_local}")
    print(f"New uploads: {uploaded_count}")
    print(f"Skipped (already exists): {skipped_count}")
    print(f"GDrive mapping file saved to: {JSON_MAP_PATH}")

if __name__ == '__main__':
    if '--fix-permissions' in sys.argv:
        # Bulk-fix permissions for all existing files in the folder
        print("=== Fix-permissions mode ===")
        creds = get_credentials()
        service = build('drive', 'v3', credentials=creds)
        folder_id = get_or_create_covers_folder(service)
        remote_files = get_remote_files_in_folder(service, folder_id)
        import threading
        from concurrent.futures import ThreadPoolExecutor, as_completed
        
        thread_local = threading.local()
        def get_thread_service():
            if not hasattr(thread_local, "service"):
                thread_local.service = build('drive', 'v3', credentials=creds)
            return thread_local.service

        def fix_worker(item):
            fname, fid = item
            local_svc = get_thread_service()
            local_svc.permissions().create(
                fileId=fid,
                body={'role': 'reader', 'type': 'anyone'}
            ).execute()
            return fname

        total = len(remote_files)
        items = list(remote_files.items())
        print(f"Setting public permissions on {total} files using 20 workers...")
        
        fixed = 0
        errors = 0
        with ThreadPoolExecutor(max_workers=20) as executor:
            futures = {executor.submit(fix_worker, item): item for item in items}
            for i, future in enumerate(as_completed(futures), 1):
                fname, fid = futures[future]
                try:
                    future.result()
                    fixed += 1
                except Exception as e:
                    errors += 1
                    print(f"  Failed {fname}: {e}")
                
                if i % 100 == 0 or i == total:
                    print(f"  [{i}/{total}] processed (Fixed={fixed}, Errors={errors})", flush=True)
                    
        print(f"\nDone! Total={total} Fixed={fixed} Errors={errors}")
    else:
        main()
