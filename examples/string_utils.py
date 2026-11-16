
def reverse_string(text):
    """Reverse a string."""
    return text[::-1]


def is_palindrome(text):
    """Check whether a string is a palindrome, ignoring case and spaces."""
    normalized = text.lower().replace(" ", "")
    return normalized == normalized[::-1]
