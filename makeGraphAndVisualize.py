import func_defs
#from func_defs import all_in_one
import sys


def loader():
    start_date, end_date = sys.argv[1:]
    func_defs.all_in_one(start_date,end_date)



# arg1 : start_date
# arg2 : end_date
if __name__ == '__main__':
    loader()
