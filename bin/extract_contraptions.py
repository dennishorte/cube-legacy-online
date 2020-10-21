import sys
from app.util.cockatrice import contraption_extractor


fin_name = sys.argv[1]

print(contraption_extractor(fin_name))
