"""This file is part of nand2tetris, as taught in The Hebrew University,
and was written by Aviv Yaish according to the specifications given in  
https://www.nand2tetris.org (Shimon Schocken and Noam Nisan, 2017)
and as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0 
Unported License (https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing
import re  # re is Regular expression operations

class JackTokenizer:
    """Removes all comments from the input stream and breaks it
    into Jack language tokens, as specified by the Jack grammar.
    
    An Xxx .jack file is a stream of characters. If the file represents a
    valid program, it can be tokenized into a stream of valid tokens. The
    tokens may be separated by an arbitrary number of space characters, 
    newline characters, and comments, which are ignored. There are three 
    possible comment formats: /* comment until closing */ , /** API comment 
    until closing */ , and // comment until the line’s end.

    ‘xxx’: quotes are used for tokens that appear verbatim (‘terminals’);
    xxx: regular typeface is used for names of language constructs 
    (‘non-terminals’);
    (): parentheses are used for grouping of language constructs;
    x | y: indicates that either x or y can appear;
    x?: indicates that x appears 0 or 1 times;
    x*: indicates that x appears 0 or more times.

    ** Lexical elements **
    The Jack language includes five types of terminal elements (tokens).
    1. keyword: 'class' | 'constructor' | 'function' | 'method' | 'field' | 
    'static' | 'var' | 'int' | 'char' | 'boolean' | 'void' | 'true' | 'false' 
    | 'null' | 'this' | 'let' | 'do' | 'if' | 'else' | 'while' | 'return'
    2. symbol:  '{' | '}' | '(' | ')' | '[' | ']' | '.' | ',' | ';' | '+' | 
    '-' | '*' | '/' | '&' | '|' | '<' | '>' | '=' | '~' | '^' | '#'
    3. integerConstant: A decimal number in the range 0-32767.
    4. StringConstant: '"' A sequence of Unicode characters not including 
    double quote or newline '"'
    5. identifier: A sequence of letters, digits, and underscore ('_') not 
    starting with a digit.


    ** Program structure **
    A Jack program is a collection of classes, each appearing in a separate 
    file. The compilation unit is a class. A class is a sequence of tokens 
    structured according to the following context free syntax:
    
    class: 'class' className '{' classVarDec* subroutineDec* '}'
    classVarDec: ('static' | 'field') type varName (',' varName)* ';'
    type: 'int' | 'char' | 'boolean' | className
    subroutineDec: ('constructor' | 'function' | 'method') ('void' | type) 
    subroutineName '(' parameterList ')' subroutineBody
    parameterList: ((type varName) (',' type varName)*)?
    subroutineBody: '{' varDec* statements '}'
    varDec: 'var' type varName (',' varName)* ';'
    className: identifier
    subroutineName: identifier
    varName: identifier

    ** Statements **
    statements: statement*
    statement: letStatement | ifStatement | whileStatement | doStatement | 
    returnStatement
    letStatement: 'let' varName ('[' expression ']')? '=' expression ';'
    ifStatement: 'if' '(' expression ')' '{' statements '}' ('else' '{' 
    statements '}')?
    whileStatement: 'while' '(' 'expression' ')' '{' statements '}'
    doStatement: 'do' subroutineCall ';'
    returnStatement: 'return' expression? ';'


    ** Expressions **
    expression: term (op term)*
    term: integerConstant | stringConstant | keywordConstant | varName | 
    varName '['expression']' | subroutineCall | '(' expression ')' | unaryOp 
    term
    subroutineCall: subroutineName '(' expressionList ')' | (className | 
    varName) '.' subroutineName '(' expressionList ')'
    expressionList: (expression (',' expression)* )?
    op: '+' | '-' | '*' | '/' | '&' | '|' | '<' | '>' | '='
    unaryOp: '-' | '~' | '^' | '#'
    keywordConstant: 'true' | 'false' | 'null' | 'this'
    
    If you are wondering whether some Jack program is valid or not, you should
    use the built-in JackCompiler to compiler it. If the compilation fails, it
    is invalid. Otherwise, it is valid.
    """
    # the set_of_symbols in jack language:
    set_of_symbols = \
        {'{', '}', '(', ')', '[', ']', '.', ',', ';', '+', '-', '*', '/', '&', '<', '>', '=', '~', '^', '#'}

    # set_of_keywords in jack language:
    set_of_keywords = \
        {"class", "constructor", "function", "method", "field", "static", "var", "int", "char", "void",
         "boolean", "true", "false", "null", "this", "let", "do", "if", "else", "while", "return"}
    # I used:
    # https://docs.python.org/3/library/re.html
    # https: // pynative.com / python - regex - compile /
    regex_for_integers = r'\d+'
    regex_for_strings = r'"[^"\n]*"'
    regex_for_identifiers = r'[\w]+'
    regex_for_keywords = '(?!\w)|'.join(set_of_keywords) + '(?!\w)'
    regex_for_symbols = '[' + re.escape('|'.join(set_of_symbols)) + ']'

    def __init__(self, input_stream: typing.TextIO) -> None:
        """Opens the input stream and gets ready to tokenize it.

        Args:
            input_stream (typing.TextIO): input stream.
        """
        # Your code goes here!
        # A good place to start is:

        self.input_lines = input_stream.read()
        # remove all the comments from the input_lines
        self.__remove_comments_from_input()
        self.tokens_list = []
        # init the tokens_list:
        self.__init_tokens_list()
        self.current_token = ""

    def has_more_tokens(self) -> bool:
        """Do we have more tokens in the input?

        Returns:
            bool: True if there are more tokens, False otherwise.
        """
        # Your code goes here!
        return len(self.tokens_list) > 0

    def advance(self) -> None:
        """Gets the next token from the input and makes it the current token. 
        This method should be called if has_more_tokens() is true. 
        Initially there is no current token.
        """
        # Your code goes here!
        self.current_token = self.tokens_list[0]
        del self.tokens_list[0]
        return

    def token_type(self) -> str:
        """
        called only if current type is not ""
        Returns:
            str: the type of the current token, can be
            "KEYWORD", "SYMBOL", "IDENTIFIER", "INT_CONST", "STRING_CONST"
        """
        # Your code goes here!
        return self.current_token[0]

    def keyword(self) -> str:
        """
        Returns:
            str: the keyword which is the current token.
            Should be called only when token_type() is "KEYWORD".
            Can return "CLASS", "METHOD", "FUNCTION", "CONSTRUCTOR", "INT", 
            "BOOLEAN", "CHAR", "VOID", "VAR", "STATIC", "FIELD", "LET", "DO", 
            "IF", "ELSE", "WHILE", "RETURN", "TRUE", "FALSE", "NULL", "THIS"
        """
        keyword = self.current_token[1]
        if keyword == "class":
            return "CLASS"

        if keyword == "method":
            return "METHOD"

        if keyword == "function":
            return "FUNCTION"

        if keyword == "constructor":
            return "CONSTRUCTOR"

        if keyword == "int":
            return "INT"

        if keyword == "boolean":
            return "BOOLEAN"

        if keyword == "char":
            return "CHAR"

        if keyword == "void":
            return "VOID"

        if keyword == "var":
            return "VAR"

        if keyword == "static":
            return "STATIC"

        if keyword == "field":
            return "FIELD"

        if keyword == "let":
            return "LET"

        if keyword == "do":
            return "DO"

        if keyword == "if":
            return "IF"

        if keyword == "else":
            return "ELSE"

        if keyword == "while":
            return "WHILE"

        if keyword == "return":
            return "RETURN"

        if keyword == "true":
            return "TRUE"

        if keyword == "false":
            return "FALSE"

        if keyword == "null":
            return "NULL"

        if keyword == "this":
            return "THIS"

    def symbol(self) -> str:
        """
        Returns:
            str: the character which is the current token.
            Should be called only when token_type() is "SYMBOL".
        """
        # Your code goes here!
        symbol = self.current_token[1]
        return symbol

    def identifier(self) -> str:
        """
        Returns:
            str: the identifier which is the current token.
            Should be called only when token_type() is "IDENTIFIER".
        """
        # Your code goes here!
        identifier = self.current_token[1]
        return identifier

    def int_val(self) -> int:
        """
        Returns:
            str: the integer value of the current token.
            Should be called only when token_type() is "INT_CONST".
        """
        # Your code goes here!
        int_val = int(self.current_token[1])
        return int_val

    def string_val(self) -> str:
        """
        Returns:
            str: the string value of the current token, without the double 
            quotes. Should be called only when token_type() is "STRING_CONST".
        """
        # Your code goes here!
        string_val = self.current_token[1]
        return string_val

    ######################################
    # helpers- not part of the API:
    #######################################
    def find_next_token(self) -> tuple:
        """
        function that finds the next token
        Returns:
            if there are more tokens return the next token, else return ("PROBLEM", 0)
        """
        # Your code goes here!
        if self.has_more_tokens():
            return self.tokens_list[0]
        else:
            return ("PROBLEM", 0)

    def __remove_comments_from_input(self):
        """
        remove all types of comments from self.input_lines
        Returns:
           Nothing- just change self.input_lines to not contain comments
        """
        lines_without_comments = ""
        curr_index = 0
        end_index = 0
        input_lines_length = len(self.input_lines)
        while curr_index < input_lines_length:
            curr_character = self.input_lines[curr_index]
            result = self.update_lines_according_character(curr_character, curr_index, end_index)
            curr_index = result[0]
            end_index = result[1]
            lines_without_comments += result[2]
        # updates input lines to be without comments
        self.input_lines = lines_without_comments

        return

    def update_lines_according_character(self, curr_character, curr_index, end_index):
        """
        update lines_without_comments according to the curr character
        Returns: tupple includes:
            updated curr_index,
            updated end_index,
           string to add to the lines_without_comments
        """
        if curr_character == "\"":
            end_index = self.input_lines.find("\"", curr_index + 1)
            return end_index + 1, end_index, self.input_lines[curr_index:end_index + 1]
        elif curr_character == "/":
            if self.input_lines[curr_index + 1] == "/":
                end_index = self.input_lines.find("\n", curr_index + 1)
                return end_index + 1, end_index, " "
            elif self.input_lines[curr_index + 1] == "*":
                end_index = self.input_lines.find("*/", curr_index + 1)
                return end_index + 2, end_index, " "
            else:
                return curr_index + 1, end_index, self.input_lines[curr_index]
        else:
            return curr_index + 1, end_index, self.input_lines[curr_index]

    def __init_tokens_list(self):
        """
        init the tokens list
        Returns:
           Nothing- just init this.tokens_list
        """
        pattern_for_word = \
            re.compile(
                self.regex_for_keywords +
                '|' + self.regex_for_symbols +
                '|' + self.regex_for_integers +
                '|' + self.regex_for_strings +
                '|' + self.regex_for_identifiers)
        words_matches_of_pattern = pattern_for_word.findall(self.input_lines)
        for each_word in words_matches_of_pattern:
            if re.match(self.regex_for_keywords, each_word) is not None:
                self.tokens_list.append(("KEYWORD", each_word))

            elif re.match(self.regex_for_symbols, each_word) is not None:
                self.tokens_list.append(("SYMBOL", each_word))

            elif re.match(self.regex_for_integers, each_word) is not None:
                self.tokens_list.append(("INT_CONST", each_word))

            elif re.match(self.regex_for_strings, each_word) is not None:
                self.tokens_list.append(("STRING_CONST", each_word[1:-1]))

            else:
                self.tokens_list.append(("IDENTIFIER", each_word))
