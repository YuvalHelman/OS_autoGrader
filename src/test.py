import subprocess as sp


def func():
    try:
        p = sp.Popen(args=['./bash_insmod'], )
        p.wait()
        if (p.returncode == 1):
            print("insmod failed for user: %s", "test")
            return 1
    except OSError as e:
        print("OSError : ", e)
        return 1
    return 0


if __name__ == '__main__':
    print(func())
