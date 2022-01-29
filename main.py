def Input():
    n,m,k,r = map(int, input().split())
    d = [[None]] + [list(map(int, input().split())) for i in range(n)]
    uv = [[None]] +[list(map(int, input().split())) for i in range(r)]
    return n,m,k,r,d,uv

score = 0
k,r = 0,0
def main():
    global score,k,r
    n,m,k,r,d,uv = Input()

    score = n+m+k+r
    print(score)

if __name__ == '__main__':
    main()
