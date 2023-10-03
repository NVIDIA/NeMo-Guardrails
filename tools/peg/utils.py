import re

def add_empty_lines(input_str):
    # Replace "INDENT" with "INDENT\n"
    input_str = input_str.replace("INDENT", "INDENT\n")

    # Replace "DEDENT" with "\nDEDENT\n"
    input_str = input_str.replace("DEDENT", "\nDEDENT\n")
    # Replace more than two consecutive newlines with just one newline
    output_str = re.sub(r'\n{3,}', '\n\n', input_str)

    return output_str

def transform_to_braces(input_text):
    lines = input_text.split("\n")

    # Get base indentation level
    base_indentation = len(lines[0]) - len(lines[0].lstrip())

    transformed_lines = []
    previous_indentation = base_indentation
    indentation_stack = [base_indentation]

    for line in lines:
        stripped_line = line.lstrip()
        current_indentation = len(line) - len(stripped_line)

        if not stripped_line:
            continue  # Skip empty lines

        # If the current line's indentation is greater than the previous line's, add INDENT
        if current_indentation > previous_indentation:
            transformed_lines.append("INDENT\n" + stripped_line)
            indentation_stack.append(current_indentation)
        # If the current line's indentation is less than the previous line's, add DEDENT
        elif current_indentation < previous_indentation:
            while indentation_stack and current_indentation < indentation_stack[-1]:
                transformed_lines.append("DEDENT")
                indentation_stack.pop()
            transformed_lines.append(stripped_line)
        else:
            transformed_lines.append(stripped_line)

        previous_indentation = current_indentation

    # Ensure we close all open INDENTS with DEDENTS
    while indentation_stack and len(indentation_stack) > 1:
        transformed_lines.append("DEDENT")
        indentation_stack.pop()

    intermediate_repr =  "\n".join(transformed_lines)

    return add_empty_lines(intermediate_repr)
