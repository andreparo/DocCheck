


class DraftStaticClass:
    """Another class to test doccheck"""

    @classmethod
    def lets_Hope_This_Test_Work(cls) -> None:
        """CHECK IF YOU SEE THIS TEST RUNNING
        >>test: "DOCCHECK WORKS WITH DECORATORS" == "DOCCHECK WORKS WITH DECORATORS"
        """
        return None
    


    """
    >>test: "DOCCHECK WORKS OUTSIDE FUNCTIONS" == "DOCCHECK WORKS OUTSIDE FUNCTIONS"
    """



"""
    >>test: "\n\n\n\n\n YOU SHOULD NOT SEE THIS, DOCCHECK IS NOT SUPPOSED TO RUN OUTSIDE CLASSES" = None
    """