import sys
try:
    from vnstock import Quote, Trading
    print("Available in Quote:", [m for m in dir(Quote) if not m.startswith('_')])
    from vnstock.api.company import Company
    print("Available in Company:", [m for m in dir(Company) if not m.startswith('_')])
except Exception as e:
    print(e)
