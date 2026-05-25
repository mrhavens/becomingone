import os

def fix_file(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    if 'utcnow()' not in content:
        return

    # Replace utcnow()
    new_content = content.replace('datetime.now(timezone.utc)', 'datetime.now(timezone.utc)')

    # Add timezone import if missing
    if 'from datetime import timezone' not in new_content and 'import timezone' not in new_content:
        # Try to find a good place to insert it
        lines = new_content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('from datetime import') or line.startswith('import datetime'):
                lines.insert(i + 1, 'from datetime import timezone')
                break
        else:
            # If no datetime import found, just put it at the top
            lines.insert(0, 'from datetime import timezone')
        new_content = '\n'.join(lines)

    with open(filepath, 'w') as f:
        f.write(new_content)
    print(f"Fixed {filepath}")

def main():
    root_dir = '/tmp/becomingone'
    for dirpath, _, filenames in os.walk(root_dir):
        if '.git' in dirpath:
            continue
        for f in filenames:
            if f.endswith('.py'):
                fix_file(os.path.join(dirpath, f))

if __name__ == '__main__':
    main()
