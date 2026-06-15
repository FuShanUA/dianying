import os

def main():
    app_path = '/Users/shanfu/cc/Projects/movie-database-revival/app.py'
    with open(app_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    in_details_else = False
    
    for idx, line in enumerate(lines):
        line_num = idx + 1
        
        # Check for start of col_details else block
        if line_num == 1071: # '    else:'
            new_lines.append(line)
            # Insert the scrollable container declaration with proper indentation
            new_lines.append("        with st.container(height=820, border=False):\n")
            in_details_else = True
            continue
            
        if in_details_else:
            # Add 4 extra spaces of indentation to all lines inside the else block
            if line.strip():
                new_lines.append("    " + line)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)
            
    with open(app_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print("Indentation applied successfully!")

if __name__ == '__main__':
    main()
