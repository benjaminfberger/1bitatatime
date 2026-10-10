# 1bitatatime (v1.0.0)

This language explores the limist of compuutational minimalism by emulating logic gates. 

This repository has the transpiler, vscode syntax highligher and documentation.

The runtime enforces a strict **64-bit virtual hardware environment** mapped entirely within a single physical CPU register, requiring zero RAM allocation overhead during active execution layers.

Every program in 1bitatatime language runs in O(N) time and O(1) space. 

## repository structure

- `src/`: source code
- `examples/`: example code
- `vscode/benjaminfberger.1bitatatime-1.0.0`: vscode syntax highlighting extension
- `docs/`: documentation on hardware contraints and language structure
- `misc/`: old c code

## examples

### example: full adder ([examples/fadder.1bit](/examples/swap.1bit))

```text
in: a b cin
sum1 = a ^ b
sum = sum1 ^ cin
carry1 = a & b
carry2 = sum1 & cin
cout = carry1 | carry2
out: sum cout
```

### example: swap values x and y ([examples/swap.1bit](/examples/xor.1bit))

```text
in: x y
temp = x
x = y
y = temp
out: x y
```
Check out more [examples](/examples/examples.md). 

## compiling

To compile a source file using the 1bit transpiler, run
```bash
./1bit swap.1bit

# Expected output
success[1b000]: compiled binary: swap.exe
```

### running the generated binary
The tra will create a binary. Execute it by passing space separated binary values (`1` or `0`) corresponding to your `in:` variables:

```bash
# Running with inputs x=1, y=0
./fadder 1 0 1

# Expected output:
output: 0 1
```

### prerequisites
To run the transpiler, you must have the .net 10 sdk installed as well as gcc

For comprehensive information on errors or warnings, or if you just want to learn more, refer to the [documentation](/docs/docs.md), or read the [wiki](https://esolangs.org/wiki/1bitatatime).
