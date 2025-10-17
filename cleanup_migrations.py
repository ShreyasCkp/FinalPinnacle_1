import os

def cleanup_migrations(project_root):
    for root, dirs, files in os.walk(project_root):
        if 'migrations' in dirs:
            migrations_dir = os.path.join(root, 'migrations')
            print(f'Cleaning migrations in: {migrations_dir}')
            for filename in os.listdir(migrations_dir):
                file_path = os.path.join(migrations_dir, filename)
                if filename != '__init__.py' and (filename.endswith('.py') or filename.endswith('.pyc')):
                    try:
                        os.remove(file_path)
                        print(f'Deleted: {file_path}')
                    except Exception as e:
                        print(f'Failed to delete {file_path}: {e}')
            # Optionally remove __pycache__ inside migrations
            pycache_dir = os.path.join(migrations_dir, '__pycache__')
            if os.path.exists(pycache_dir):
                try:
                    for f in os.listdir(pycache_dir):
                        os.remove(os.path.join(pycache_dir, f))
                    os.rmdir(pycache_dir)
                    print(f'Deleted __pycache__ in {migrations_dir}')
                except Exception as e:
                    print(f'Failed to delete __pycache__ in {migrations_dir}: {e}')

if __name__ == '__main__':
    project_root = os.path.dirname(os.path.abspath(__file__))
    cleanup_migrations(project_root)
    print('Migration cleanup complete!')
