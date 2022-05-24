class Book:
    '''
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
    '''

    def __init__(self) -> None:
        brown = "\33[38;2;160;82;45m\33[1m"
        gold = "\33[38;5;229m"
        white = "\33[38;5;231m"
        white_back = "\33[47m"
        end = "\33[0m"
        self.book_parts = {
            "top_level": {
                "text": "_",
                "term_text": "\33[37;1m_\33[0m",
                "html_color": "_"
            },
            "top_start": {
                "text": ".-/|",
                "term_text": f"{brown}.{end}{gold}-/{end}|"
            },
            "top_middle": {
                "text": " V ",
                "term_text": " V "
            },
            "top_end": {
                "text": "|\\-.\n",
                "term_text": f"|{end}{gold}\\-{end}{brown}.{end}\n",
            },
            "middle_start": {
                "text": "||||",
                "term_text": f"{brown}|{end}{gold}||{end}|"
            },
            "middle": {
                "text": " | ",
                "term_text": " │ "
            },
            "middle_end": {
                "text": "|||┃",
                "term_text": f"{white}|{end}{gold}||{end}{brown}|{end}"
            },
            "bottom_single_pg_start": {
                "text": "||||",
                "term_text": f"{brown}|{end}{gold}||{end}{white}|{end}",
            },
            "bottom_single_pg_middle": {
                "text": " | ",
                "term_text": " │ "
            },
            "bottom_single_pg_end": {
                "text": "||||",
                "term_text": f"|{end}{gold}||{end}{brown}|{end}",
            },
            "bottom_multi_pg_left": {
                "text": "||/=",
                "term_text": f"{brown}|{end}{gold}|/="
            },
            "bottom_multi_pg_middle": {
                "text": "\\|/",
                "term_text": f"\33[0m\\|/{gold}"
            },
            "bottom_multi_pg_end": {
                "text": "=\\||",
                "term_text": f"=\\|{end}{brown}|{end}"
            },
            "bottom_final_pg_left": {
                "text": "`---",
                "term_text": f"{brown}`---"
            },
            "bottom_final_pg_middle": {
                "text": "~___~",
                "term_text": "~___~"
            },
            "bottom_final_pg_end": {
                "text": "---𝅪",
                "term_text": f"---𝅪{end}"
            }
        }

    def get_book_parts(self) -> dict():
        return self.book_parts
