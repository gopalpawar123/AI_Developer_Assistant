
def reverse_string(text):
    """Reverse a string."""

    if not isinstance(text, str):
        raise TypeError("Input must be a string.")

    return text[::-1]


def is_palindrome(text):
    """Check whether a string is a palindrome, ignoring case and spaces."""

    if not isinstance(text, str):
        raise TypeError("Input must be a string.")

    normalized = text.lower().replace(" ", "")

    return normalized == normalized[::-1]
