# 1bitatatime language documentation

The language is evaluated sequentially line-by-line. All lines following a `#` are treated as comments.

### keywords
- **`in:`** declares variables as inputs at the top of the file.
- **`out:`** declares variables as outputs at the bottom of the file.
- **`=`** assigns a value to a variable.
- **`!&`** or **`nand`** evaluates bitwise nand logic: `!(A & B)`.

### constants
`true` and `1` are interchangable. 

`false` and `0` are interchangable. 

### example: full adder [examples/fadder.1bit](examples/swap.1bit))

```text
in: a b cin
sum1 = a ^ b
sum = sum1 ^ cin
carry1 = a & b
carry2 = sum1 & cin
cout = carry1 | carry2
out: sum cout
```
Check out more [examples](/examples/examples.md). 
## compiling

To compile a source file using the 1bit transpiler, run
```bash
./1bit fadder.1bit

# Expected output
success[1b000]: compiled binary: fadder.exe
```

### running the generated binary
The compiler will create a binary. Execute it by passing space separated binary values (`1` or `0`) corresponding to your `in:` variables:

```bash
# Running with inputs x=1, y=0
./fadder 1 0 1

# Expected output:
output: 0 1
```

## hardware constraints
Everything runs inside a single 64-bit register in the CPU.

Bits 0 and 1 in the virtual ram are reserved for the language. 

A maximum of 62 variables can be declared in total. 

## errors

### fatal errors
`error [1b001]: no arguments given`
 - **cause**: 1bit compiler run with no source filepath
 - **fix**: pass a valid source as a argument for 1bit compiler

`error [1b002]: gcc not installed`
 - **cause**: path to gcc compiler could not be found
 - **fix**: ensure gcc is installed by running `gcc --version` in the folder you intend to compile from

`error [1b003]: gcc failed to compile`
- **cause**: 1bit compiler successfully created the intermediate c code, but gcc could not compile it
- **fix**: pray your code works next time

`error [1b101]: not enough inputs`
- **cause**: not enough inputs passed into compiled binary
- **fix**: pass the correct number of inputs into the compiled program, specified by the number of variables after `in:`, on the first line of your program

`error [1b102]: code must end with out:`
- **cause**: `out:` keyword not present in your program
- **fix**: add `out:` to the last line of your program

`error [1b103]: source empty`
- **cause**: pass empty source file to 1bit compiler 
- **cause**: pass source file that does not contain `in:`
- **fix**: ensure your program is not empty and contains `in:` at the start of your program

`error [1b201]: out of memory`
- **cause**: exceed 62 assignable variable limit
- **fix**: try to recycle your variables by resetting their values with `myVariable = 0`

`error [1b202]: variable undefined`
- **cause**: using an undefined varible as an operand
- **fix**: define variables before using them as operands

### non-fatal errors (warnings)

`warn [1b401]: source does not end in .1bit`
- **cause**: source file does not end in `.1bit`
- **fix**: rename your source file to end in `.1bit`

`warn [1b402]: program contains no inputs`
- **cause**: no variables declared as inputs in the `in:` block of your program
- **fix**: declare inputs in the `in:` block of your program

`warn [1b403]: program contains no outputs`
- **cause**: no variables declared as outputs in the `out:` block of your program
- **fix**: declare outputs in the `out` block of your program