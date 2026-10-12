import sys
import typing
from dataclasses import dataclass as dc

# DISCLAIMER:
#  the following source file as been authored entirely by human hand.
#  i object to the use of generative LLMs in programming.


stream_content = []
stream_index = 0
def tokenize(path):
    with open(path, 'r') as f:
        src = f.read()

    tokens = []
    for line in src.split('\n'):
        tokens += line.split(' ')
        if line: tokens.append('\n')

    tokens = list(filter(lambda x: bool(x), tokens))

    # make sure file is terminated by a line-feed
    if tokens and tokens[-1] != '\n':
        tokens.append('\n')

    global stream_content
    stream_content = tokens


def tok_has(): return stream_index < len(stream_content)
def tok_peek():
    if tok_has(): 
        return stream_content[stream_index]
    else:
        print("error: unexpected end of token stream")

        import traceback
        traceback.print_stack()
        sys.exit(1)
def tok_pop():
    global stream_index
    t = tok_peek()
    stream_index += 1
    return t
def tok_expect(ref):
    tok = tok_pop()
    if tok != ref:
        print(f"error: expected `{ref}` but got `{tok}`")
        sys.exit(1)


variable = {'0': 0, '1': 1}

# look up and allocate if not present
# variable bit offset into r15
def lookup(name):
    if name not in variable:
        if len(variable) >= 64:
            print("error: more than 64 variables used.")
            sys.exit(1)
        variable[name] = len(variable)
    return variable[name]

output = []
def emit(x):
    output.append(x)

@dc
class AstLeaf:
    content : str

    @classmethod
    def parse(cls):
        return cls(tok_pop())

    def compile(self):
        self.load()
        
    def load(self):
        offset = lookup(self.content)
        emit('mov rax, r15')
        emit(f'shr rax, {offset}')
        emit('and rax, 1')

    def store(self):
        if self.content in ('0', '1'):
            print(f"warning: assigning to built-in variable `{self.content}`")
        offset = lookup(self.content)

        #reset bit in r15
        mask = ((1 << 64) - 1) ^ (1 << offset)
        emit(f"and r15, {mask}")

        #set bit in r15
        emit(f"shl rax, {offset}")
        emit(f"or r15, rax")


@dc
class AstBinary:
    left  : typing.Any
    right : typing.Any
    op    : str

    def compile(self):
        self.left .load()
        emit('mov bl, al')
        self.right.load()

        negate = False
        if self.op[0] == '!': 
            self.op = self.op[1]
            negate = True

        match self.op[0]:
            case '&': emit('and al, bl')
            case '|': emit('or  al, bl')
            case '^': emit('xor al, bl')

        if negate:
            emit('xor al, 1')

@dc
class AstNot:
    expr : typing.Any

    def compile(self):
        self.expr.load()
        emit('xor al, 1')

def parse_expression():
    if tok_peek() == '!':
        tok_pop()
        return AstNot(AstLeaf.parse())

    left = AstLeaf.parse()
    op = tok_peek()
    if op in ('!&', '!|', '!^', '|', '&', '^'):
        tok_pop()
        right = AstLeaf.parse()
        left = AstBinary(left, right, op)

    return left


@dc
class AstStmt:
    dst : AstLeaf
    src : typing.Any

    @classmethod
    def parse(cls, ):
        dst = AstLeaf.parse()
        tok_expect('=')
        src = parse_expression()
        tok_expect('\n')
        return cls(dst, src)

    def compile(self):
        self.src.compile()
        self.dst.store()


flag_has_inputs = False

@dc
class AstProg:
    ins   : list[str]
    outs  : list[str]
    stmts : list[AstStmt]

    @staticmethod
    def remain():
        tail = []
        while tok_peek() != '\n':
            tail.append(tok_pop())
        tok_expect('\n')
        return tail

    @classmethod
    def parse(cls, ):
        stmts = []
        ins = None
        outs = None
        while tok_has():
            match tok_pop():
                case 'in:' : ins  = cls.remain()
                case 'out:': outs = cls.remain()
                case x:
                    global stream_index
                    stream_index -= 1 #un-pop token
                    stmts.append(AstStmt.parse())

        return cls(ins, outs, stmts)

    def compile(self):
        emit("section '.text' code readable executable")
        emit("start:")

        # r15 stores variables.
        emit("mov r15, 0")

        if self.ins:
            global flag_has_inputs
            flag_has_inputs = True

            emit("call [GetCommandLineA]")
            for i, name in enumerate(self.ins):
                offset = lookup(name)
                emit("call next_argument")
                emit(f"shl rbx, {offset}")
                emit("or r15, rbx")
            emit('arg_done:\n')

        emit('; --- program start ---\n')
        for stmt in self.stmts:
            stmt.compile()
        emit('; --- program end ---\n')

        if self.outs:
            for i, name in enumerate(self.outs):
                offset = lookup(name)
                output = 8 + 2 * i
                emit(f"mov rax, r15")
                emit(f"shr rax, {offset}")
                emit(f"and rax, 1")
                emit(f"add al, '0'")
                emit(f"mov [output + {output}], al")

            emit("mov rcx, -11")
            emit("call [GetStdHandle]")
            emit("mov rcx, rax")
            emit("mov rdx, output")
            emit(f"mov r8, {output + 1}")
            emit("mov r9, 0")
            emit("call [WriteFile]")

        emit("mov rcx, 0")
        emit("call [ExitProcess]")

        emit("section '.data' readable writable")
        emit("output: db 'output:                            '")

def finalize(body):
    arg_reader = """
next_argument:
.find_space:
    inc rax
    cmp byte [rax], 0
    je arg_done
    cmp byte [rax], ' '
jne .find_space

.find_char:
    inc rax
    mov bl, byte [rax]
    cmp bl, 0
    je arg_done
    cmp bl, ' '
je .find_char
    sub bl, '0'
    ret
    """

    with open('build.asm', 'w') as f:
        f.write(f"""
    format PE64
    entry start

{arg_reader if flag_has_inputs else ""}
{body}

    section '.idata' import data readable writeable
        dd 0,0,0,rva kernel_name,rva kernel_table
        dd 0,0,0,0,0

        kernel_table:
            ExitProcess     dq rva _ExitProcess
            GetCommandLineA dq rva _GetCommandLineA
            GetStdHandle    dq rva _GetStdHandle
            WriteFile       dq rva _WriteFile
            dq 0

        kernel_name: db 'KERNEL32.DLL',0
        _ExitProcess    : db 0,0,'ExitProcess',0
        _GetCommandLineA: db 0,0,'GetCommandLineA',0
        _GetStdHandle   : db 0,0,'GetStdHandle',0
        _WriteFile      : db 0,0,'WriteFile',0
    """)

def main():
    if len(sys.argv) < 2:
        print("Error: No source path provided.\nUsage: python3 compiler.py <path>")
        sys.exit(1)

    tokenize(sys.argv[1])
    root = AstProg.parse()
    
    root.compile()
    finalize("\n".join(output))

if __name__ == '__main__':
    main()
