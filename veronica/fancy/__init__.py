try:

    from art import text2art as text2art
    from art import tprint as tprint
except ImportError:
    raise ImportError("art is not installed., Please install it using pip insall art")