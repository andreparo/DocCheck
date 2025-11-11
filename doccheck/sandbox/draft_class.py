class DraftClass:
    """
    >>example1: cls(2,6,"hello")
    """

    def __init__(self, a: int, b: int, c: str):
        """"""
        self.a: int = a
        self.b: int = b
        self.c: str = c


    def draft_Format(self, additional_text: str="") -> str:
        """
        
        >>test: cls.example1.draft_Format() == "2.6.hello."
        >>test: cls.example1.draft_Format("ADD") == "2.6.hello.ADD"
        >>error: 10/0
        """
        return f"{self.a}.{self.b}.{self.c}.{additional_text}"