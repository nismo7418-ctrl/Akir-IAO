with open('streamlit_app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the try block
try_start = content.find('try:')
except_start = content.find('\nexcept', try_start)

if try_start != -1 and except_start != -1:
    before_try = content[:try_start]
    try_block = content[try_start:except_start]
    after_except = content[except_start:]
    
    # Indent the try block (except the 'try:' line itself)
    lines = try_block.split('\n')
    indented_lines = [lines[0]]  # 'try:' line
    for line in lines[1:]:
        if line.strip():  # Only indent non-empty lines
            indented_lines.append('    ' + line)
        else:
            indented_lines.append(line)
    
    indented_try_block = '\n'.join(indented_lines)
    
    # Write back
    with open('streamlit_app.py', 'w', encoding='utf-8') as f:
        f.write(before_try + indented_try_block + after_except)
    
    print("Indentation fixed")
else:
    print("Could not find try-except block")