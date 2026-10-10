import sys
import typing
from dataclasses import dataclass as dc

def tokenize(path):
    with open(path, 'r') as f:
        src = f.read()

    tokens = []
    for line in src.split('\n'):
        tokens += line.split(' ')
        if line: tokens.append('\n')

    return list(filter(lambda x: bool(x), tokens))

variable = {}
def alloc(name):
    if name not in variable:
        variable[name] = len(variable) + 1

@dc
class AstLeaf:
    content : str
    kind : typing.Literal['lit', 'var']

    @classmethod
    def parse(cls, stream):
        content = stream.pop(0)
        kind = 'lit' if content.isdigit() else 'var'
        return cls(content, kind)

    def compile(self):
        match self.kind:
            case 'lit': return f'mov al, {self.content}\n'
            case 'var': return f'mov al, [rbp-{variable[self.content]}]\n'

@dc
class AstNand:
    left  : AstLeaf
    right : AstLeaf

    def compile(self):
        return  (
            self.left .compile() + 'mov bl, al\n' +
            self.right.compile() + 'and al, bl\nxor al, 1\n'
        )

@dc
class AstStmt:
    dst : str
    src : AstNand | AstLeaf

    @classmethod
    def parse(cls, stream):
        dst = stream.pop(0)
        assert stream.pop(0) == '='
        src = AstLeaf.parse(stream)

        if stream[0] == '!&':
            stream.pop(0)
            left = src
            right = AstLeaf.parse(stream)
            src = AstNand(left, right)

        alloc(dst)
        assert stream.pop(0) == '\n'
        return cls(dst, src)

    def compile(self):
        return self.src.compile() + f'mov [rbp-{variable[self.dst]}], al\n'

@dc
class AstProg:
    ins   : list[str]
    outs  : list[str]
    stmts : list[AstStmt]

    @staticmethod
    def remain(stream):
        tail = []
        while stream[0] != '\n':
            tail.append(stream.pop(0))
        stream.pop(0) # consume newline
        return tail

    @classmethod
    def parse(cls, stream):
        stmts = []
        ins = None
        outs = None
        while stream:
            match stream.pop(0):
                case 'in:' : ins  = cls.remain(stream)
                case 'out:': outs = cls.remain(stream)
                case x:
                    stream.insert(0, x)
                    stmts.append(AstStmt.parse(stream))
        if ins:
            for var in ins: 
                alloc(var)

        return cls(ins, outs, stmts)

    def compile(self):
        output = ''
        output += "section '.text' code readable executable\n"
        output += "start:\n"
        output += "mov rbp, rsp\n"
        for _ in variable:
            output += "push 0\n"

        if self.ins:
            output += "call [GetCommandLineA]\n"
            for i, name in enumerate(self.ins):
                vaddr = variable[name]
                output += "call next_argument\n"
                output += f"mov byte [rbp-{vaddr}], bl\n"
            output += 'arg_done:\n'

        output += '; --- program start ---\n'
        for stmt in self.stmts:
            output += stmt.compile()
        output += '; --- program end ---\n'

        if self.outs:
            for i, name in enumerate(self.outs):
                vaddr = variable[name]
                offset = 8 + 2 * i
                output += f"mov al, byte [rbp-{vaddr}]\n"
                output += f"add al, '0'\n"
                output += f"mov [output + {offset}], al\n"

            output += "mov rcx, -11\n"
            output += "call [GetStdHandle]\n"
            output += "mov rcx, rax\n"
            output += "mov rdx, output\n"
            output += f"mov r8, {offset + 1}\n"
            output += "mov r9, 0\n"
            output += "call [WriteFile]\n"

        output += "mov rcx, 0\n"
        output += "call [ExitProcess]\n"

        output += "section '.data' readable writable\n"
        output += "output: db 'output:                            '\n"
        return output

def finalize(body):
    with open('build.asm', 'w') as f:
        f.write(f"""
    format PE64
    entry start

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

    stream = tokenize(sys.argv[1])
    root = AstProg.parse(stream)
    
    output = root.compile()
    finalize(output)

if __name__ == '__main__':
    main()
