import argparse
import hashlib
import shutil
import time
import os


TIME = time.strftime('%Y-%m-%d %H:%M:%S')


def check_md5(file_path):
    '''Calculate MD5 hash of the file'''
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

  
def synchronize(source_dir, replica_dir, log_file):
    '''Main synch logic'''
    source_tree = os.walk(source_dir)
    replica_tree = os.walk(replica_dir)
    source_path, source_dirs, source_files = next(source_tree, (None, [], []))
    replica_path, replica_dirs, replica_files = next(replica_tree, (None, [], []))

    #   Deleting redundant items from replica
    for replica_name in replica_dirs:
        replica_child_path = os.path.join(replica_path, replica_name)
        if replica_name not in source_dirs:
            mess = f"[{TIME}] Deleting directory: {replica_child_path}"
            shutil.rmtree(replica_child_path)
            print(mess)
            log(log_file, mess)

    for replica_name in replica_files:
        replica_child_path = os.path.join(replica_path, replica_name)
        if replica_name not in source_files:
            mess = f"[{TIME}] Deleting file: {replica_child_path}"
            os.remove(replica_child_path)
            print(mess)
            log(log_file, mess)

    #   Creating new dir in replica
    for source_name in source_dirs:
        source_child_path = os.path.join(source_path, source_name)
        if source_name not in replica_dirs:
            replica_child_path = os.path.join(replica_path, source_name)
            mess = f"[{TIME}] Creating directory: {replica_child_path}"
            shutil.copytree(source_child_path, replica_child_path)
            print(mess)
            log(log_file, mess)

        else:
            replica_child_path = os.path.join(replica_path, source_name)
            synchronize(source_child_path, replica_child_path, log_file)

    #   Creating and updating the files in replica
    for source_name in source_files:
        source_child_path = os.path.join(source_path, source_name)
        if source_name not in replica_files:
            replica_child_path = os.path.join(replica_path, source_name)
            mess = f"[{TIME}] Copying file: {replica_child_path}"
            shutil.copy2(source_child_path, replica_child_path)
            print(mess)
            log(log_file, mess)

        elif check_md5(source_child_path) != check_md5(os.path.join(replica_path, source_name)):
            replica_child_path = os.path.join(replica_path, source_name)
            mess = f"[{TIME}] Updating file: {replica_child_path}"
            shutil.copy2(source_child_path, replica_child_path)
            print(mess)
            log(log_file, mess)     

        #   Additional check for the latest time of change
        elif os.path.getmtime(source_child_path) != os.path.getmtime(os.path.join(replica_path, source_name)):
            replica_child_path = os.path.join(replica_path, source_name)
            mess = f"[{TIME}] Updating file: {replica_child_path}"
            shutil.copy2(source_child_path, replica_child_path)
            print(mess)
            log(log_file, mess) 


def synchronize_folders(source_dir, replica_dir, log_file, interval):
    '''Set the time of synchronization'''
    while True:
        synchronize(source_dir, replica_dir, log_file)
        time.sleep(interval)

  
def log(log_file, message):
    '''Log into specified file'''
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(message + '\n')


def main():
    '''Main function with user interactions'''
    parser = argparse.ArgumentParser(description='Synchronize source and replica folders.')
    parser.add_argument('source_folder', type=str, help='Path to source folder')
    parser.add_argument('replica_folder', type=str, help='Path to replica folder')
    parser.add_argument('log_file', type=str, help='Path to log file')
    parser.add_argument('interval', type=int, default=10, help='Synchronization interval in seconds (default: 10 seconds)')

    args = parser.parse_args()

    while True:
        try:
            mess = f"[{TIME}] Synchronization started with interval of {args.interval} seconds"
            print(mess)
            log(args.log_file, mess)
            synchronize_folders(args.source_folder, args.replica_folder, args.log_file, args.interval)

        except KeyboardInterrupt:
            print('Synchronization ends')
            break

        except Exception as e:
            print('An error occurred:', e)


if __name__ == '__main__':
    main()