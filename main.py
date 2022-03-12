# write your code here.

TURN_MAX = 300

def main():
    n = int(input())
    nz = [list(map(int,input().split())) for i in range(n)]
    m = int(input())
    mz = [list(map(int,input().split())) for i in range(m)]

    if n==20: _ = 1/0
    if n==10:
        import time
        time.sleep(3)


    for turn in range(TURN_MAX):
        print("."*m, flush=True)
        _ = input()
    import random
    return random.randint(0, 100)
    
if __name__ == '__main__':
    main()
