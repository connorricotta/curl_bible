from werkzeug.datastructures import ImmutableMultiDict


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
                "text": "|",
                "term_text": "|"
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


class Options:
    width = 80
    length = 20
    text_only = False
    text_color = True
    options_dict = {}

    def __init__(self, options: ImmutableMultiDict) -> None:
        options_list = options.split(",")
        for option in options_list:
            if option in ['t', 'text']:
                self.text_only = True
            if option in ['nc', 'no_color']:
                self.text_color = False
            if option in ['c', 'color']:
                self.text_color = True
            if 'v' in option or 'version' in option:
                version = option.split("=")[-1]
                self.version = version
                self.options_dict['version'] = self.version
            if 'w' in option or 'width' in option:
                value = option.split("=")
                if str.isnumeric(value[-1]) and int(value[-1]) >= 0:
                    self.width = int(value[-1])
            if 'l' in option or 'length' in option:
                value = option.split("=")
                if str.isnumeric(value[-1]) and int(value[-1]) >= 0:
                    self.length = int(value[-1])
        self.options_dict['text_only'] = self.text_only
        self.options_dict['text_color'] = self.text_color
        self.options_dict['width'] = self.width
        self.options_dict['length'] = self.length

        pass

    def get_options_dict(self) -> dict:
        return self.options_dict
