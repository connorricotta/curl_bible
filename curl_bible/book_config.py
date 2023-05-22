class Book:
    """
     Standard configuration for the book. Using text escaped characters
     Quick Explainer (for future me)
     Arguments 38 and 48 (custom text-color and background)
     support either:
         • Three args (255 color)
             - 38;5;5
             - 48;5;5
         • Five args (RGB color)
             - 38;2;45;25;67
             - 48;2;45;25;67

    Escape    Ending
     Code    Character  Arg 2
      |          |        |
      V          V        V
     \33[48;5;255m \33[30;1mTest\33[0m
         Λ  Λ  Λ       Λ
         |  |  |       |
        Args 1a-1c   Arg 1
    """

    def __init__(self) -> None:
        brown = "\33[38;2;160;82;45m\33[1m"
        gold = "\33[38;5;229m"
        white = "\33[38;5;231m"
        # white_back = "\33[47m"
        end = "\33[0m"
        self.book_no_color = {
            "top_level": "_",
            "top_start": ".-/|",
            "top_middle": " V ",
            "top_end": "|\\-.\n",
            "middle_start": "||||",
            "middle": "|",
            "middle_end": "||||",
            "bottom_single_pg_start": "||||",
            "bottom_single_pg_middle": " | ",
            "bottom_single_pg_end": "||||",
            "bottom_multi_pg_left": "||/=",
            "bottom_multi_pg_middle": "\\|/",
            "bottom_multi_pg_end": "=\\||",
            "bottom_final_pg_left": "`---",
            "bottom_final_pg_middle": "~___~",
            "bottom_final_pg_end": "---𝅪",
        }

        self.book_color = {
            "top_level": "\33[37;1m_\33[0m",
            "top_start": f"{brown}.{end}{gold}-/{end}|",
            "top_middle": " V ",
            "top_end": f"|{end}{gold}\\-{end}{brown}.{end}\n",
            "middle_start": f"{brown}|{end}{gold}||{end}|",
            "middle": "|",
            "middle_end": f"{white}|{end}{gold}||{end}{brown}|{end}",
            "bottom_single_pg_start": f"{brown}|{end}{gold}||{end}{white}|{end}",
            "bottom_single_pg_middle": " | ",
            "bottom_single_pg_end": f"|{end}{gold}||{end}{brown}|{end}",
            "bottom_multi_pg_left": f"{brown}|{end}{gold}|/=",
            "bottom_multi_pg_middle": f"\33[0m\\|/{gold}",
            "bottom_multi_pg_end": f"=\\|{end}{brown}|{end}",
            "bottom_final_pg_left": f"{brown}`---",
            "bottom_final_pg_middle": "~___~",
            "bottom_final_pg_end": f"---𝅪{end}",
        }

    def get_no_color(self) -> dict():
        return self.book_no_color

    def get_color(self) -> dict():
        return self.book_color
