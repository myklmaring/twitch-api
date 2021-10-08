import time
import json

def foo():
    result = []
    try:
        # Long running code
        for i in range(10000):
            result.append(i)
            time.sleep(0.1)
        return result
    except KeyboardInterrupt:
        # Code to "save"
        mydict = {'result': result}
        with open('a.json', 'w') as f:
            json.dump(mydict, f)

        print('dictionary saved')

        return result


if __name__ == "__main__":
    print(foo())
