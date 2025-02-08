
import datetime


from_date= datetime.datetime.now()-datetime.timedelta(days=30)
from_date = from_date.strftime('%Y-%m-%d')
to_date = datetime.datetime.now().strftime('%Y-%m-%d')

print(from_date,    to_date)