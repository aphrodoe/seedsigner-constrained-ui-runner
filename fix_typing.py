import os
import re

typing_pattern = re.compile(r"^\s*from\s+typing\s+import\s+(.*?)$", re.MULTILINE)
threading_pattern = re.compile(r"^\s*import\s+threading\b", re.MULTILINE)

for root, _, files in os.walk("src"):
    for file in files:
        if file.endswith(".py"):
            path = os.path.join(root, file)
            with open(path, "r") as f:
                content = f.read()
            
            new_content = content
            
            # Fix typing
            def replace_typing(match):
                indent = match.group(0).split("from")[0]
                imports = match.group(1).replace(" ", "").split(",")
                res = f"{indent}typing = __import__('typing')\n"
                for imp in imports:
                    if imp:
                        res += f"{indent}{imp} = typing.{imp}\n"
                return res.rstrip()
                
            if typing_pattern.search(new_content):
                new_content = typing_pattern.sub(replace_typing, new_content)
                
            # Fix threading (in audio_renderer.py)
            def replace_threading(match):
                indent = match.group(0).split("import")[0]
                return f"{indent}threading = __import__('threading')"
                
            if threading_pattern.search(new_content):
                new_content = threading_pattern.sub(replace_threading, new_content)
                
            if new_content != content:
                with open(path, "w") as f:
                    f.write(new_content)
                print(f"Fixed {path}")
