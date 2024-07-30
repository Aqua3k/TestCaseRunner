import sys

n,m = map(int,input().split())
print(f"This is debug message! n = {n}, m = {m}", file=sys.stderr)
print(n+m * 2)
