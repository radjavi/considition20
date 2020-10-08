all: t1 t2

t1:
	python main.py training1

t2:
	python main.py training2

py3t1:
	python3 main.py training1

py3t2:
	python3 main.py training2

py3c1:
	python3 main.py Gothenburg

py3c2:
	python3 main.py Kiruna

py3c3:
	python3 main.py Visby

py3c4:
	python3 main.py London