""" Regex implementation using finite state machine """

#pylint:skip-file

from __future__ import annotations
from abc import ABC, abstractmethod

class State(ABC):
    def __init__(self) -> None:
        self.next_states: list[State] = []

    @abstractmethod
    def check_self(self, char: str) -> bool | State:
        """
        function checks whether occured character is handled by current ctate
        """
        pass

    def check_next(self, next_char: str) -> State | Exception:
        for state in self.next_states:
            if state.check_self(next_char):
                return state
        raise NotImplementedError("rejected string")

class StartState(State):
    """ Starting state of the FSM """
    def __init__(self):
        super().__init__()
    def check_self(self, char: str) -> bool:
        return False

class TerminationState(State):
    """ Termination state of the FSM """
    def __init__(self):
        super().__init__()
    def check_self(self, char: str) -> bool:
        return False

class DotState(State):
    """ State representing a dot in the regex """
    def __init__(self):
        super().__init__()
    def check_self(self, char: str) -> bool:
        return True

class AsciiState(State):
    """ State representing an ASCII character in the regex """
    def __init__(self, symbol: str) -> None:
        super().__init__()
        self.pattern = symbol
    def check_self(self, curr_char: str) -> bool:
        return curr_char == self.pattern

class CharClassState(State):
    """ State representing bracketed characters in the regex """
    def __init__(self, chars: set[str]) -> None:
        super().__init__()
        self.pattern = chars
    def check_self(self, curr_char: str) -> bool:
        return curr_char in self.pattern

class StarState(State):
    """ State representing a star in the regex, can contain a different state  """
    def __init__(self, base_state: State):
        super().__init__()
        self.pattern = getattr(base_state, 'pattern', None)
    def check_self(self, char: str) -> bool | State:

        for state in self.next_states:
            if state is self:
                continue
            res = state.check_self(char)
            if res:
                return state if isinstance(res, State) else state

        if self.pattern is None or (isinstance(self.pattern, set) and char in self.pattern) or char == self.pattern:
            return True
        return False

class PlusState(State):
    """ State representing a plus in the regex, can contain a different state  """
    def __init__(self, base_state: State):
        super().__init__()
        self.pattern = getattr(base_state, 'pattern', None)
        self.cycle_count = 0
    def check_self(self, char: str) -> bool | State:

        if self.cycle_count > 0:
            for state in self.next_states:
                if state is self:
                    continue
                res = state.check_self(char)
                if res:
                    return state if isinstance(res, State) else state

        if self.pattern is None or (isinstance(self.pattern, set) and char in self.pattern) or char == self.pattern:
            self.cycle_count += 1
            return True
        return False

class RegexFSM:
    def __init__(self, regex_expression: str) -> None:
        self.pattern = regex_expression
        self.start_state = StartState()
        self.termination_state = TerminationState()
        self.states: list[State] = [self.start_state, self.termination_state]

        previous_state = self.start_state
        index = 0
        while index < len(regex_expression):
            current_char = regex_expression[index]

            if current_char == '[':
                class_end_index = regex_expression.find(']', index)

                if class_end_index == -1:
                    raise ValueError()

                raw_class = regex_expression[index+1:class_end_index]
                character_set: set[str] = set()

                range_index = 0
                while range_index < len(raw_class):

                    if range_index + 2 < len(raw_class) and raw_class[range_index+1] == '-':
                        range_start = raw_class[range_index]
                        range_end = raw_class[range_index+2]
                        character_set.update(
                            chr(code) for code in range(ord(range_start), ord(range_end) + 1)
                        )
                        range_index += 3
                    else:
                        character_set.add(raw_class[range_index])
                        range_index += 1

                base_state = CharClassState(character_set)
                next_character = regex_expression[class_end_index + 1] if class_end_index + 1 < len(regex_expression) else None
                index = class_end_index
            else:
                next_character = regex_expression[index + 1] if index + 1 < len(regex_expression) else None
                if current_char == '.':
                    base_state = DotState()
                else:
                    base_state = AsciiState(current_char)

            if next_character == '*':
                state = StarState(base_state)
                index += 1
            elif next_character == '+':
                state = PlusState(base_state)
                index += 1
            else:
                state = base_state

            previous_state.next_states.append(state)
            self.states.append(state)
            if isinstance(state, (StarState, PlusState)):
                state.next_states.append(state)

            previous_state = state
            index += 1

        previous_state.next_states.append(self.termination_state)

    def reset(self):
        for state in self.states:
            if isinstance(state, PlusState):
                state.cycle_count = 0

    def check_string(self, input_string: str) -> bool:
        self.reset()
        current = self.start_state
        for char in input_string:
            if not char.isascii():
                return False
            for state in current.next_states:
                result = state.check_self(char)
                if result:
                    current = result if isinstance(result, State) else state
                    break
            else:
                return False
        return any(isinstance(st, TerminationState) for st in current.next_states)


if __name__ == "__main__":
    def check_given_regex():
        # Checks for given regex pattern

        regex_pattern = "a*4.+hi"
        regex_compiled = RegexFSM(regex_pattern)
        print(regex_compiled.check_string("aaaaaa4uhi"))# True
        print(regex_compiled.check_string("4uhi"))# True
        print(regex_compiled.check_string("meow"))# False
        print("")

        print(regex_compiled.check_string("4xhi"))# True
        print(regex_compiled.check_string("a4xhi"))# True
        print(regex_compiled.check_string("aa4xhi"))# True
        print(regex_compiled.check_string("aaa4xhi"))# True
        print("")

        print(regex_compiled.check_string("a4xhi"))# True
        print(regex_compiled.check_string("a4xyhi"))# True
        print(regex_compiled.check_string("a4xyzhi"))# True
        print(regex_compiled.check_string("a4hi"))# False
        print("")

        print(regex_compiled.check_string("a4xhii"))# False
        print(regex_compiled.check_string("a4xh"))# False
        print(regex_compiled.check_string("b4xhi"))# False
        print(regex_compiled.check_string("a5xhi"))# False
        print(regex_compiled.check_string(""))# False
        print("")

        print(regex_compiled.check_string("a4!hi"))# True
        print(regex_compiled.check_string("a4 hi"))# True
        print(regex_compiled.check_string("a4\thi"))# True
        print(regex_compiled.check_string("a4\nhi"))# True
        print("")

        print(regex_compiled.check_string("aaa4xyz123hi"))# True
        print(regex_compiled.check_string("a4hihi"))# True
        print(regex_compiled.check_string("4hellohi"))# True
        print("")

    def check_bracket_regex():
        # Checks for additional bracket regex pattern

        regex_compiled = RegexFSM("[a-z]*4[0-9]+hi")

        print(regex_compiled.check_string("aaa4123hi"))# True
        print(regex_compiled.check_string("4xhi"))# False
        print(regex_compiled.check_string("zzz4 123hi"))# False
        print(regex_compiled.check_string("4hi"))# False
        print("")

        comp2 = RegexFSM("[abcXYZ0-3]+")
        print(comp2.check_string("abcaXYZ0123"))# True
        print(comp2.check_string(""))# False
        print("")

        comp3 = RegexFSM("[!@#]*.+")
        print(comp3.check_string("!!@!foo"))# True
        print(comp3.check_string("foo"))# True
        print(comp3.check_string(""))# False
        print("")

        comp4 = RegexFSM("[0-9]*")
        print(comp4.check_string("123456"))# True
        print(comp4.check_string("12a456"))# False
        print("")

    check_given_regex()
    check_bracket_regex()