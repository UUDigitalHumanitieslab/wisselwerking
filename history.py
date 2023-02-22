import sys
from wisselwerking.history import read_history
previous_years_dir = sys.argv[1]

history = read_history(previous_years_dir)
history.to_csv()
