import re
# --- VALIDATION HELPER APPLICATION ---

def is_required(value):
    return value is not None and str(value).strip() != ""


def is_numeric(value, min_val=None, max_val=None):
    try:
        num = float(value)
        if min_val is not None and num < min_val:
            return False
        if max_val is not None and num > max_val:
            return False
        return True
    except (ValueError, TypeError):
        return False


def is_integer(value, min_val=None, max_val=None):
    try:
        num = int(value)
        if min_val is not None and num < min_val:
            return False
        if max_val is not None and num > max_val:
            return False
        return True
    except (ValueError, TypeError):
        return False


def is_percentage(value):
    try:
        val = float(value)
        return 0 <= val <= 100
    except (ValueError, TypeError):
        return False


def is_valid_email(email):
    pattern = r"^[\\w\\.-]+@[\\w\\.-]+\\.\\w+$"
    return re.match(pattern, email) is not None


def is_in_choices(value, choices):
    return value in choices


def validate_length(value, min_len=1, max_len=255):
    return value is not None and min_len <= len(str(value).strip()) <= max_len
