"""
Style Class Documentation:

Description:
    The `Style` class defines ANSI escape codes for different text colors, including default white, as well as
    codes for underline and reset. These codes can be used to format text when printing to the console.

Usage:
    - To apply a specific color or style, use the class attributes. For example, `print(style.RED + "This is red text" + style.RESET)`.

Attributes:
    - BLACK (str): ANSI escape code for black text.
    - RED (str): ANSI escape code for red text.
    - GREEN (str): ANSI escape code for green text.
    - YELLOW (str): ANSI escape code for yellow text.
    - BLUE (str): ANSI escape code for blue text.
    - MAGENTA (str): ANSI escape code for magenta text.
    - CYAN (str): ANSI escape code for cyan text.
    - WHITE (str): ANSI escape code for white text.
    - UNDERLINE (str): ANSI escape code for underlined text.
    - RESET (str): ANSI escape code to reset text formatting.

Example:
    ```python
    print(style.MAGENTA + "This text is in magenta." + style.RESET)
    print(style.UNDERLINE + "This text is underlined." + style.RESET)
    print("This is default white text.")
    ```

getTimestamp Function Documentation:

Description:
    The `getTimestamp` function retrieves the current timestamp in the format "[HH:MM:SS.mmm]". It updates the 
    global variable `currentTimeStamp` with the calculated timestamp.

Usage:
    - Call the function using `getTimestamp()` to update the `currentTimeStamp` variable.

Variables:
    - currentTimeStamp (str): A global variable storing the current timestamp.

Example:
    ```python
    getTimestamp()
    print("Current timestamp:", currentTimeStamp)
    ```

Note: Ensure that the `datetime` module is imported for the code to work properly.
"""


class style(): # Class of different text colours - default is white
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    UNDERLINE = '\033[4m'
    RESET = '\033[0m'
