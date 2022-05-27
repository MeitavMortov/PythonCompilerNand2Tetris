"""This file is part of nand2tetris, as taught in The Hebrew University,
and was written by Aviv Yaish according to the specifications given in  
https://www.nand2tetris.org (Shimon Schocken and Noam Nisan, 2017)
and as allowed by the Creative Common Attribution-NonCommercial-ShareAlike 3.0 
Unported License (https://creativecommons.org/licenses/by-nc-sa/3.0/).
"""
import typing


class SymbolTable:
    """A symbol table that associates names with information needed for Jack
    compilation: type, kind and running index. The symbol table has two nested
    scopes (class/subroutine).
    """
    # constant represents the index of type in a tuple n a symbol table:
    INDEX_FOR_TYPE_OF_COMMAND = 0

    # constant represents the index of kind in a tuple n a symbol table:
    INDEX_FOR_KIND_OF_COMMAND = 1

    # constant represents the index of index in a tuple n a symbol table:
    INDEX_FOR_INDEX_OF_COMMAND = 2

    def __init__(self) -> None:
        """Creates a new empty symbol table."""
        self.counters_dictionary = {
            "var_counter": 0,
            "arg_counter": 0,
            "field_counter": 0,
            "static_counter": 0,
            "if_counter": 0,
            "while_counter": 0
        }
        self.class_scope_table = {}
        self.subroutines_scope_table = {}
        self.current_table = self.class_scope_table

    def start_subroutine(self) -> None:
        """Starts a new subroutine scope (i.e., resets the subroutine's 
        symbol table).
        """
        # resets the subroutines_scope_table:
        self.subroutines_scope_table = {}
        self.current_table = self.subroutines_scope_table
        # reset the counters_state_dictionary:
        self._reset_counters()

    def define(self, name: str, type: str, kind: str) -> None:
        """Defines a new identifier of a given name, type and kind and assigns 
        it a running index. "STATIC" and "FIELD" identifiers have a class scope, 
        while "ARG" and "VAR" identifiers have a subroutine scope.

        Args:
            name (str): the name of the new identifier.
            type (str): the type of the new identifier.
            kind (str): the kind of the new identifier, can be:
            "STATIC", "FIELD", "ARG", "VAR".
        """

        if kind == "STATIC":
            self.class_scope_table[name] = \
                (type, kind, self.counters_dictionary["static_counter"])
            self.counters_dictionary["static_counter"] += 1

        elif kind == "FIELD":
            self.class_scope_table[name] = \
                (type, kind,  self.counters_dictionary["field_counter"])
            self.counters_dictionary["field_counter"] += 1

        elif kind == "ARG":
            self.current_table[name] =\
                (type, kind, self.counters_dictionary["arg_counter"])
            self.counters_dictionary["arg_counter"] += 1

        elif kind == "VAR":
            self.current_table[name] = \
                (type, kind, self.counters_dictionary["var_counter"])
            self.counters_dictionary["var_counter"] += 1

    def var_count(self, kind: str) -> int:
        """
        Args:
            kind (str): can be "STATIC", "FIELD", "ARG", "VAR".

        Returns:
            int: the number of variables of the given kind already defined in 
            the current scope.
        """
        if kind == "STATIC" or kind == "FIELD":
            table_to_count = self.class_scope_table
        else:
            table_to_count = self.current_table

        num_of_vars_of_given_kind = 0

        for (key, value) in table_to_count.items():
            if value[1] == kind:
                num_of_vars_of_given_kind += 1

        return num_of_vars_of_given_kind

    def kind_of(self, name: str) -> str:
        """
        Args:
            name (str): name of an identifier.

        Returns:
            str: the kind of the named identifier in the current scope, or None
            if the identifier is unknown in the current scope.
        """
        return self._helper_finds_identifier_details(name, self.INDEX_FOR_KIND_OF_COMMAND)

    def type_of(self, name: str) -> str:
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            str: the type of the named identifier in the current scope. Or None
            if the identifier is unknown in the current scope.
        """
        return self._helper_finds_identifier_details(name, self.INDEX_FOR_TYPE_OF_COMMAND)

    def index_of(self, name: str) -> int:
        """
        Args:
            name (str):  name of an identifier.

        Returns:
            int: the index assigned to the named identifier. Or -1
            if the identifier is unknown in the current scope.
        """
        result = self._helper_finds_identifier_details(name, self.INDEX_FOR_INDEX_OF_COMMAND)
        # if result is NONE  the identifier is unknown in the current scope:
        if result == "NONE":
            return -1

        return int(result)

    def change_to_the_class_scope(self):
        """
        change the current scope to the class scope
        """
        self.current_table = self.class_scope_table

    ######################################
    # helpers- not part of the API:
    #######################################
    def _reset_counters(self):
        """
        set the counters for the program:
         sets counters of the types:
         var arg field static
        """
        self.counters_dictionary["var_counter"] = 0
        self.counters_dictionary["arg_counter"] = 0
        self.counters_dictionary["field_counter"] = 0
        self.counters_dictionary["static_counter"] = 0
        self.counters_dictionary["if_counter"] = 0
        self.counters_dictionary["while_counter"] = 0

    def _helper_finds_identifier_details(self,name: str, index_represents_command: int) -> str:
        """
        _helper_finds_identifier_details
        helper function to the methods:
        index_of , type_of , kind_of
        Args:
            name (str):  name of an identifier.
            index_represents_command (int):
            one of:
               INDEX_FOR_TYPE_OF_COMMAND = 0
                INDEX_FOR_KIND_OF_COMMAND = 1
                INDEX_FOR_INDEX_OF_COMMAND = 2
        Returns:
            str: the type of the named identifier in the current scope. Or None
            if the identifier is unknown in the current scope.
        """
        if name in self.current_table:
            return str(self.current_table[name][index_represents_command])

        if name in self.class_scope_table:
            return str(self.class_scope_table[name][index_represents_command])

        # if reached here the identifier is unknown in the current scope:
        return "NONE"
