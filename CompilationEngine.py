"""This file is part of nand2tetris, as taught in The Hebrew University,
and was written by Aviv Yaish according to the specifications given in  
https://www.nand2tetris.org (Shimon Schocken and Noam Nisan, 2017)
and as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0 
Unported License (https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing
import JackTokenizer
import SymbolTable
import VMWriter


class CompilationEngine:
    """Gets input from a JackTokenizer and emits its parsed structure into an
    output stream.
    """
    # a dictionary of the keywords in the jack language:
    keywords_dict = {
        "CLASS": "class",
        "METHOD": "method",
        "FUNCTION": "function",
        "CONSTRUCTOR": "constructor",
        "INT": "int",
        "BOOLEAN": "boolean",
        "CHAR": "char",
        "VOID": "void",
        "VAR": "var",
        "STATIC": "static",
        "FIELD": "field",
        "LET": "let",
        "DO": "do",
        "IF": "if",
        "ELSE": "else",
        "WHILE": "while",
        "RETURN": "return",
        "TRUE": "true",
        "FALSE": "false",
        "NULL": "null",
        "THIS": "this"
    }

    def __init__(self, input_stream: "JackTokenizer", output_stream) -> None:
        """
        Creates a new compilation engine with the given input and output. The
        next routine called must be compileClass()
        :param input_stream: The input stream.
        :param output_stream: The output stream.
        """
        self._output_file = output_stream
        # inits the jack tokenizer, the vm writer and the symbol table which help to compile the input stream:
        self._jack_tokenizer = JackTokenizer.JackTokenizer(input_stream)
        self._vm_writer = VMWriter.VMWriter(output_stream)
        self._symbol_table = SymbolTable.SymbolTable()
        self._current_class_name = ""
        self._function_name = ""

    def compile_class(self) -> None:
        """Compiles a complete class."""
        # advance in order to get "class":
        self._jack_tokenizer.advance()
        #  advance in order to get class_name:
        self._current_class_name = self._advance_and_get_value_of_current_token()
        #  advance in order to get "{":
        self._jack_tokenizer.advance()
        # checks if there is / are varDec and compile them:
        if self._is_next_value_equals(self.keywords_dict["STATIC"]) or \
                self._is_next_value_equals(self.keywords_dict["FIELD"]):
            # if there are var dec compile them:
            self.compile_class_var_dec()
        # compiles all the subroutines:
        while self._is_next_value_equals(self.keywords_dict["CONSTRUCTOR"]) or \
                self._is_next_value_equals(self.keywords_dict["METHOD"]) or \
                self._is_next_value_equals(self.keywords_dict["FUNCTION"]):
            self.compile_subroutine()
        #  advance in order to get  "}":
        self._jack_tokenizer.advance()
        # close file in the end of class- assuming files are valid:
        self._close()

    def compile_class_var_dec(self) -> None:
        """Compiles a static declaration or a field declaration."""
        # Your code goes here!
        while self._is_next_value_equals(self.keywords_dict["STATIC"]) or \
                self._is_next_value_equals(self.keywords_dict["FIELD"]):
            # advance and get 'static' or 'field':
            var_kind = self._advance_and_get_value_of_current_token()
            # advance and get var_type:
            var_type = self._advance_and_get_value_of_current_token()
            # advance and get var_name:
            var_name = self._advance_and_get_value_of_current_token()
            # defines the var in the symbol table:
            self._symbol_table.define(var_name, var_type, var_kind)
            while self._is_next_value_equals(","):
                # advance and in order to get ',':
                self._jack_tokenizer.advance()
                # advance and in order to get var_name:
                var_name = self._advance_and_get_value_of_current_token()
                # defines the var in the symbol table:
                self._symbol_table.define(var_name, var_type, var_kind)
            # advance and in order to get ';':
            self._jack_tokenizer.advance()

    def compile_subroutine(self) -> None:
        """
        Compiles a complete method, function, or constructor.
        You can assume that classes with constructors have at least one field,
        you will understand why this is necessary in project 11.
        """
        #  advance in order to get subroutine's type:
        function_type = self._advance_and_get_value_of_current_token()
        #  advance in order to get subroutine's return type:
        self._jack_tokenizer.advance()
        #  advance in order to get subroutine's name:
        self._function_name = self._current_class_name + '.' + self._advance_and_get_value_of_current_token()
        self._symbol_table.start_subroutine()
        #  advance in order to get '(':
        self._jack_tokenizer.advance()
        if function_type == "METHOD":
            self._symbol_table.define(self.keywords_dict["THIS"], "self", 'ARG')
        self.compile_parameter_list()
        #  advance in order to get ')':
        self._jack_tokenizer.advance()
        # compile subroutine body:
        #  advance in order to get '{':
        self._jack_tokenizer.advance()
        while self._is_next_value_equals(self.keywords_dict["VAR"]):
            self.compile_var_dec()
        num_of_vars = self._symbol_table.var_count("VAR")
        self._vm_writer.write_function(self._function_name, num_of_vars)
        if function_type == "METHOD":
            self._vm_writer.write_push("ARG", 0)
            self._vm_writer.write_pop("POINTER", 0)
        if function_type == 'CONSTRUCTOR':
            num_of_class_vars = self._symbol_table.var_count("FIELD")
            self._vm_writer.write_push("CONST", num_of_class_vars)
            self._vm_writer.write_call("Memory.alloc", 1)
            self._vm_writer.write_pop("POINTER", 0)
        self.compile_statements()
        #  advance in order to get '}':
        self._jack_tokenizer.advance()
        self._symbol_table.change_to_the_class_scope()

    def compile_parameter_list(self) -> None:
        """Compiles a (possibly empty) parameter list, not including the 
        enclosing "()".
        """
        while not self._is_next_token_type_equals("SYMBOL"):
            # compile each parameter
            # advance and get parameter_type:
            parameter_type = self._advance_and_get_value_of_current_token()
            # advance and gets parameter_name:
            parameter_name = self._advance_and_get_value_of_current_token()
            self._symbol_table.define(parameter_name, parameter_type, "ARG")
            if self._is_next_value_equals(","):
                # advance and get: ','
                self._jack_tokenizer.advance()

    def compile_var_dec(self) -> None:
        """Compiles a var declaration."""
        var_kind = self._advance_and_get_value_of_current_token()
        # advance and get var_type:
        var_type = self._advance_and_get_value_of_current_token()
        # advance and get var_name:
        var_name = self._advance_and_get_value_of_current_token()
        # defines the var in the symbol table:
        self._symbol_table.define(var_name, var_type, var_kind)
        while self._is_next_value_equals(","):
            # advance and get ',':
            self._jack_tokenizer.advance()
            # advance and in order to get var_name:
            var_name = self._advance_and_get_value_of_current_token()
            # defines the var in the symbol table:
            self._symbol_table.define(var_name, var_type, var_kind)
        # advance and in order to get ';':
        self._jack_tokenizer.advance()

    def compile_statements(self) -> None:
        """Compiles a sequence of statements, not including the enclosing 
        "{}".
        """
        while self._is_next_value_equals(self.keywords_dict["DO"]) or \
                self._is_next_value_equals(self.keywords_dict["LET"]) or \
                self._is_next_value_equals(self.keywords_dict["IF"]) or \
                self._is_next_value_equals(self.keywords_dict["WHILE"]) or \
                self._is_next_value_equals(self.keywords_dict["RETURN"]):
            if self._is_next_value_equals(self.keywords_dict["DO"]):
                self.compile_do()
            elif self._is_next_value_equals(self.keywords_dict["LET"]):
                self.compile_let()
            elif self._is_next_value_equals(self.keywords_dict["IF"]):
                self.compile_if()
            elif self._is_next_value_equals(self.keywords_dict["WHILE"]):
                self.compile_while()
            elif self._is_next_value_equals(self.keywords_dict["RETURN"]):
                self.compile_return()

    def compile_do(self) -> None:
        """Compiles a do statement."""
        # advance and gets 'do':
        self._jack_tokenizer.advance()
        self._helper_to_compile_subroutine_call()
        self._vm_writer.write_pop("TEMP", 0)
        # advance and in order to get ';':
        self._jack_tokenizer.advance()

    def compile_let(self) -> None:
        """Compiles a let statement."""
        # advance and in order to get 'let':
        self._jack_tokenizer.advance()
        is_array_object = False
        # advance and get var_name
        var_name = self._advance_and_get_value_of_current_token()
        if self._is_next_value_equals("["):
            is_array_object = True
            self._helper_to_calculate_case_of_array(var_name)
        # advance and gets "=":
        self._jack_tokenizer.advance()
        self.compile_expression()
        self._helper_to_compile_let_according_if_is_array(is_array_object, var_name)
        # advance and in order to get ';':
        self._jack_tokenizer.advance()

    def compile_while(self) -> None:
        """Compiles a while statement."""
        while_counter_val = self._symbol_table.counters_dictionary["while_counter"]
        self._symbol_table.counters_dictionary["while_counter"] += 1
        self._vm_writer.write_label("WHILE_EXPRESSION_LABEL" + str(while_counter_val))
        # advance and get "while"
        self._jack_tokenizer.advance()
        # advance and get "("
        self._jack_tokenizer.advance()
        self.compile_expression()
        self._vm_writer.write_arithmetic("NOT")
        self._vm_writer.write_if("WHILE_FINISHED_LABEL" + str(while_counter_val))
        # advance and get ")"
        # advance and get "{"
        self._jack_tokenizer.advance()
        self._jack_tokenizer.advance()
        self.compile_statements()
        self._vm_writer.write_goto("WHILE_EXPRESSION_LABEL" + str(while_counter_val))
        self._vm_writer.write_label("WHILE_FINISHED_LABEL" + str(while_counter_val))
        # advance and get "}"
        self._jack_tokenizer.advance()

    def compile_return(self) -> None:
        """Compiles a return statement."""
        # a list of unary operations in the jack language:
        _list_of_unary_operations = ['-', '~', '^', '#']

        # a list of constant keywords in the jack language:
        _list_of_constant_keywords = ['true', 'false', 'null', 'this']

        # advance and get return:
        self._jack_tokenizer.advance()
        is_void_subroutine = True

        while self._is_next_token_type_equals("INT_CONST") or self._is_next_token_type_equals("STRING_CONST") \
                or self._is_next_token_type_equals("IDENTIFIER") or \
                (self._is_next_value_in_list(_list_of_unary_operations)) or \
                (self._is_next_value_in_list(_list_of_constant_keywords)) or \
                (self._is_next_value_equals('(')):

            is_void_subroutine = False
            self.compile_expression()

        if (is_void_subroutine):
            self._vm_writer.write_push("CONST", 0)
        self._vm_writer.write_return()
        # advance and gets ";"
        self._jack_tokenizer.advance()

    def compile_if(self) -> None:
        """Compiles a if statement, possibly with a trailing else clause."""
        # advance and get "if"
        self._jack_tokenizer.advance()
        # advance and get "("
        self._jack_tokenizer.advance()
        self.compile_expression()
        # advance and get ")"
        self._jack_tokenizer.advance()
        if_counter_val = self._symbol_table.counters_dictionary["if_counter"]
        self._symbol_table.counters_dictionary["if_counter"] += 1

        self._vm_writer.write_if('IF_TRUE_LABEL' + str(if_counter_val))
        self._vm_writer.write_goto('IF_FALSE_LABEL' + str(if_counter_val))
        self._vm_writer.write_label('IF_TRUE_LABEL' + str(if_counter_val))

        # advance and get "{"
        self._jack_tokenizer.advance()
        self.compile_statements()
        # advance and get "}"
        self._jack_tokenizer.advance()
        # compile else (if there is) block:
        self._helper_to_compile_else_block(if_counter_val)

    def compile_expression(self) -> None:
        """Compiles an expression."""
        self.compile_term()
        # a list of binary operations in the jack language:
        _list_of_binary_operations = ['+', '-', '*', '/', '|', '=', '<', '>', '&']
        while self._is_next_value_in_list(_list_of_binary_operations):
            # advance and gets the operation:
            current_operation = self._advance_and_get_value_of_current_token()
            self.compile_term()
            self._helper_writes_given_binary_operation(current_operation)

    def compile_term(self) -> None:
        """Compiles a term. 
        This routine is faced with a slight difficulty when
        trying to decide between some of the alternative parsing rules.
        Specifically, if the current token is an identifier, the routing must
        distinguish between a variable, an array entry, and a subroutine call.
        A single look-ahead token, which may be one of "[", "(", or "." suffices
        to distinguish between the three possibilities. Any other token is not
        part of this term and should not be advanced over.
        """
        # a list of unary operations in the jack language:
        _list_of_unary_operations = ['-', '~', '^', '#']
        # a list of constant keywords in the jack language:
        _list_of_constant_keywords = ['true', 'false', 'null', 'this']

        if self._is_next_token_type_equals("INT_CONST"):
            current_token_value = self._advance_and_get_value_of_current_token()
            self._vm_writer.write_push("CONST", current_token_value)

        elif self._is_next_token_type_equals("STRING_CONST"):
            self._helper_compile_string_const_in_term()

        elif self._is_next_value_in_list(_list_of_constant_keywords):
            self._helper_compile_constant_keywords_in_term()

        elif self._is_next_token_type_equals("IDENTIFIER"):
            self._helper_compile_identifier_in_term()

        elif self._is_next_value_in_list(_list_of_unary_operations):
            current_operation = self._advance_and_get_value_of_current_token()
            self.compile_term()
            self._helper_writes_given_unary_operation(current_operation)

        elif self._is_next_value_equals("("):
            # advance and get'(':
            self._jack_tokenizer.advance()
            self.compile_expression()
            # advance and get ')':
            self._jack_tokenizer.advance()

    def compile_expression_list(self) -> int:
        """Compiles a (possibly empty) comma-separated list of expressions."""

        # a list of unary operations in the jack language:
        _list_of_unary_operations = ['-', '~', '^', '#']
        # a list of constant keywords in the jack language:
        _list_of_constant_keywords = ['true', 'false', 'null', 'this']

        num_of_expressions = 0

        if self._is_next_token_type_equals("INT_CONST") or self._is_next_token_type_equals("STRING_CONST") \
                or self._is_next_token_type_equals("IDENTIFIER") or \
                (self._is_next_value_in_list(_list_of_unary_operations)) or \
                (self._is_next_value_in_list(_list_of_constant_keywords)) or \
                (self._is_next_value_equals('(')):
            self.compile_expression()
            num_of_expressions += 1

        while self._is_next_value_equals(","):
            # advance and gets ',' :
            self._jack_tokenizer.advance()
            self.compile_expression()
            num_of_expressions += 1

        return num_of_expressions


    ######################################
    # helpers- not part of the API:
    #######################################

    def _advance_and_get_value_of_current_token(self):
        """
        Function that advance the jack_tokenizer and returns tuple of the current tpe and value.
            Returns:
                A tuple of the current tpe and value.
         """
        self._jack_tokenizer.advance()
        token_type = self._jack_tokenizer.token_type()
        token_value = ""
        # if token types is KEYWORD:
        if token_type == "KEYWORD":
            token_value = self._jack_tokenizer.keyword()

        # else if token types is SYMBOL:
        elif token_type == "SYMBOL":
            token_value = self._jack_tokenizer.symbol()

        # else if token types is INT_CONST:
        elif token_type == "INT_CONST":
            token_value = str(self._jack_tokenizer.int_val())

        # else if token types is STRING_CONST:
        elif token_type == "STRING_CONST":
            token_value = self._jack_tokenizer.string_val()

        # else if token types is IDENTIFIER:
        elif token_type == "IDENTIFIER":
            token_value = self._jack_tokenizer.identifier()

        return token_value

    def _helper_to_compile_subroutine_call(self):
        """
        Function that helps compile the call of a subroutine.
         This function is used during compiling subroutine
         """
        first_part_of_name = self._advance_and_get_value_of_current_token()
        second_part_of_name = ""
        final_full_of_name = ""
        num_of_local_vars = 0
        if self._is_next_value_equals("."):
            self._jack_tokenizer.advance()
            second_part_of_name = self._advance_and_get_value_of_current_token()
            if first_part_of_name in self._symbol_table.current_table or \
                    first_part_of_name in self._symbol_table.class_scope_table:
                self._helper_push_according_symbol_table(first_part_of_name)
                final_full_of_name = \
                    self._symbol_table.type_of(first_part_of_name) + '.' + second_part_of_name
                num_of_local_vars += 1
            else:
                final_full_of_name = first_part_of_name + '.' + second_part_of_name
        else:
            self._vm_writer.write_push("POINTER", 0)
            num_of_local_vars += 1
            final_full_of_name = self._current_class_name + '.' + first_part_of_name
        self._jack_tokenizer.advance()
        num_of_local_vars += self.compile_expression_list()
        self._vm_writer.write_call(final_full_of_name, num_of_local_vars)
        # advance and gets ')':
        self._jack_tokenizer.advance()

    def _helper_to_compile_let_according_if_is_array(self, is_array_object: bool, var_name: str):
        """
         Function that helps compile the let statement in case there is an array
         in the let statement. This function is used during compiling let statement.
         """
        if is_array_object:
            self._vm_writer.write_pop("TEMP", 0)
            self._vm_writer.write_pop("POINTER", 1)
            self._vm_writer.write_push("TEMP", 0)
            self._vm_writer.write_pop("THAT", 0)
        else:
            if var_name in self._symbol_table.current_table:
                if self._symbol_table.kind_of(var_name) == "VAR":
                    self._vm_writer.write_pop("LOCAL", self._symbol_table.index_of(var_name))
                elif self._symbol_table.kind_of(var_name) == "ARG":
                    self._vm_writer.write_pop("ARG", self._symbol_table.index_of(var_name))
            else:
                if self._symbol_table.kind_of(var_name) == "STATIC":
                    self._vm_writer.write_pop("STATIC", self._symbol_table.index_of(var_name))
                else:
                    self._vm_writer.write_pop("THIS", self._symbol_table.index_of(var_name))

    def _helper_to_calculate_case_of_array(self, var_name: str):
        """
        Function that helps compile the statement in case there is an array
            in the let statement.
            This function is used during compiling statement in order to compute
            the value of the index in the array.
         """
        # advance and get "[":
        self._jack_tokenizer.advance()
        self.compile_expression()
        # advance and get "]":
        self._jack_tokenizer.advance()
        if var_name in self._symbol_table.current_table:
            if self._symbol_table.kind_of(var_name) == "VAR":
                self._vm_writer.write_push("LOCAL", self._symbol_table.index_of(var_name))
            elif self._symbol_table.kind_of(var_name) == "ARG":
                self._vm_writer.write_push("ARG", self._symbol_table.index_of(var_name))
        else:
            if self._symbol_table.kind_of(var_name) == "STATIC":
                self._vm_writer.write_push("STATIC", self._symbol_table.index_of(var_name))
            else:
                self._vm_writer.write_push("THIS", self._symbol_table.index_of(var_name))
        self._vm_writer.write_arithmetic("ADD")

    def _helper_to_compile_else_block(self, if_counter_val: str):
        """
        Function that helps compile if to check  and exute if  there is an else block.
            This function is used during compiling if statement in order to compile
            all the else block if it exists.
         """
        if self._is_next_value_equals(self.keywords_dict["ELSE"]):
            self._vm_writer.write_goto('IF_FINISH_LABEL' + str(if_counter_val))
            self._vm_writer.write_label('IF_FALSE_LABEL' + str(if_counter_val))
            # advance and get "else"
            self._jack_tokenizer.advance()
            # advance and get "{"
            self._jack_tokenizer.advance()
            self.compile_statements()
            # advance and get "}"
            self._jack_tokenizer.advance()
            self._vm_writer.write_label('IF_FINISH_LABEL' + str(if_counter_val))
        else:
            self._vm_writer.write_label('IF_FALSE_LABEL' + str(if_counter_val))

    def _helper_writes_given_binary_operation(self, current_operation: str):
        """
         Function that helps compile the given binary operation.
                Args:
                one operation from:
                '+' | '-' | '*' | '/' | '&' | '|' | '<' | '>' | '='
         """
        if current_operation == '+':
            self._vm_writer.write_arithmetic("ADD")

        elif current_operation == '-':
            self._vm_writer.write_arithmetic("SUB")

        elif current_operation == '=':
            self._vm_writer.write_arithmetic("EQ")

        elif current_operation == '<':
            self._vm_writer.write_arithmetic("LT")

        elif current_operation == '>':
            self._vm_writer.write_arithmetic("GT")

        elif current_operation == '|':
            self._vm_writer.write_arithmetic("OR")

        elif current_operation == '&':
            self._vm_writer.write_arithmetic("AND")

        elif current_operation == '*':
            self._vm_writer.write_call('Math.multiply', 2)

        elif current_operation == '/':
            self._vm_writer.write_call('Math.divide', 2)

    def _helper_writes_given_unary_operation(self, current_operation: str):
        """
        Function that helps compile the given unary operation.
                Args:
                one operation from:
                '-' | '~' | '^' | '#'
         """
        if current_operation == '-':
            self._vm_writer.write_arithmetic("NEG")
        elif current_operation == '~':
            self._vm_writer.write_arithmetic("NOT")
        elif current_operation == '^':
            self._vm_writer.write_arithmetic("SHIFTLEFT")
        elif current_operation == '#':
            self._vm_writer.write_arithmetic("SHIFTRIGHT")

    def _helper_compile_string_const_in_term(self):
        """
        Function that helps compile term in case of string const in the term
         it is called only if compile term needs to compile const string.
         """
        current_token_value = self._advance_and_get_value_of_current_token()
        self._vm_writer.write_push("CONST", len(current_token_value))
        self._vm_writer.write_call("String.new", 1)
        for each_char in current_token_value:
            self._vm_writer.write_push("CONST", ord(each_char))
            self._vm_writer.write_call("String.appendChar", 2)

    def _helper_compile_constant_keywords_in_term(self):
        """
        Function that helps compile term in case of constant keywords in the term
        it is called only if compile term needs to compile a constant keyword.
         """
        current_token_value = self._advance_and_get_value_of_current_token()
        if current_token_value == "THIS":
            self._vm_writer.write_push("POINTER", 0)
        else:
            self._vm_writer.write_push("CONST", 0)
            if current_token_value == "TRUE":
                self._vm_writer.write_arithmetic("NOT")

    def _helper_compile_identifier_in_term(self):
        """
        Function that helps compile term in case of identifier in the term
        it is called only if compile term needs to compile a identifier.
         """
        is_array_object = False
        num_of_locals = 0
        current_name = self._advance_and_get_value_of_current_token()
        if self._is_next_value_equals("["):
            is_array_object = True
            self._helper_to_calculate_case_of_array(current_name)
        if self._is_next_value_equals("("):
            num_of_locals += 1
            self._vm_writer.write_push("POINTER", 0)
            # advance and gets "("
            self._jack_tokenizer.advance()
            num_of_locals += self.compile_expression_list()
            # advance and gets ")"
            self._jack_tokenizer.advance()
            func_name_to_call = self._current_class_name + "." + current_name
            self._vm_writer.write_call(func_name_to_call, num_of_locals)
        elif self._is_next_value_equals("."):
            self._helper_compile_identifier_function_call_in_term(current_name, num_of_locals)

        else:
            self._helper_compile_identifier_array_and_vars_in_term(current_name, is_array_object)

    def _helper_compile_identifier_function_call_in_term(self, current_name: str, num_of_locals: int):
        """
        Function that helps _helper_compile_identifier_in_term in
        case of function call in the identifier that in the term
        it is called only if compile term needs to compile a identifier that
        contains call to a subroutine.
        Arguments:
                str: current_name that represents prt of the identifier
                int: num_of_locals number represent the num of locals variables

         """
        # advance and gets "."
        self._jack_tokenizer.advance()
        second_part_of_name = self._advance_and_get_value_of_current_token()
        if current_name in self._symbol_table.current_table or \
                current_name in self._symbol_table.class_scope_table:
            self._helper_push_according_symbol_table(current_name)
            current_name = \
                self._symbol_table.type_of(current_name) + '.' + second_part_of_name
            num_of_locals += 1
        else:
            current_name = current_name + '.' + second_part_of_name
        # advance and gets "("
        self._jack_tokenizer.advance()
        num_of_locals += self.compile_expression_list()
        # advance and gets ")"
        self._jack_tokenizer.advance()
        self._vm_writer.write_call(current_name, num_of_locals)

    def _helper_compile_identifier_array_and_vars_in_term(self, current_name: str, is_array_object: bool):
        """
        Function that helps _helper_compile_identifier_in_term in
        case of array or vars in the identifier that in the term
        it is called only if compile term needs to compile a identifier that
        contains array or vars.
        Arguments:
                str: current_name that represents prt of the identifier
                boolean: is_array_object represent the answer if it compiles an array.
         """
        if is_array_object:
            self._vm_writer.write_pop("POINTER", 1)
            self._vm_writer.write_push("THAT", 0)
        elif current_name in self._symbol_table.current_table:
            current_name_index = self._symbol_table.index_of(current_name)
            if self._symbol_table.kind_of(current_name) == "VAR":
                self._vm_writer.write_push("LOCAL", current_name_index)
            elif self._symbol_table.kind_of(current_name) == "ARG":
                self._vm_writer.write_push("ARG", current_name_index)
        else:
            current_name_index = self._symbol_table.index_of(current_name)
            if self._symbol_table.kind_of(current_name) == "STATIC":
                self._vm_writer.write_push("STATIC", current_name_index)
            else:
                self._vm_writer.write_push("THIS", current_name_index)

    def _helper_push_according_symbol_table(self, first_part_of_name):
        """
        Function that helps compile subroutine or term that contains identifier in
        case of need to push a name according to its index in the symbol table.
        it is called only if compile term needs to push a name according to its index in the symbol table.
        Arguments:
                str: first_part_of_name that represents part of the name that needed to
                be pushed according to the symbol table.
         """
        if first_part_of_name in self._symbol_table.current_table:
            if self._symbol_table.kind_of(first_part_of_name) == "VAR":
                self._vm_writer.write_push("LOCAL", self._symbol_table.index_of(first_part_of_name))
            elif self._symbol_table.kind_of(first_part_of_name) == "ARG":
                self._vm_writer.write_push("ARG", self._symbol_table.index_of(first_part_of_name))
        else:
            if self._symbol_table.kind_of(first_part_of_name) == "STATIC":
                self._vm_writer.write_push("STATIC", self._symbol_table.index_of(first_part_of_name))
            else:
                self._vm_writer.write_push("THIS", self._symbol_table.index_of(first_part_of_name))


    def _close(self) -> None:
        """Closes the output file."""
        self._output_file.close()

    def _is_next_value_in_list(self, list_to_check):
        """ Function that return an boolean answer on the question:
              Is the next token's value in the given list?
            Returns:
                boolean: answer to Is the next token's value in the given list?
         """
        token_type, token_value = self._jack_tokenizer.find_next_token()
        return list_to_check.count(token_value) > 0

    def _is_next_value_equals(self, value):
        """ Function that return an boolean answer on the question:
              Is the next token's value is equals to value?
            Returns:
                boolean: answer to Is the next token's value is equals to value?
         """
        token_type, token_value = self._jack_tokenizer.find_next_token()
        return str(token_value) == value

    def _is_next_token_type_equals(self, possible_token):
        """ Function that return an boolean answer on the question:
              Is the next token's type is equals to the type of the possible token?
            Returns:
                boolean: answer to Is the next token's type is equals to the type of the possible token?
         """
        token_type, token_value = self._jack_tokenizer.find_next_token()
        return token_type == possible_token
