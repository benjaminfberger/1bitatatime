# 1bitatatime example code

### swap values x and y ([swap.1bit](/examples/swap.1bit))

```text
in: x y
temp = x
x = y
y = temp
out: x y
```

### full adder ([fadder.1bit](/examples/xor.1bit))

```text
in: x y
w = x !& y
x = x !& w
y = y !& w
x = x !& y
out: x
```