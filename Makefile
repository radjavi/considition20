all: t1 t2

t1:
	python main.py training1

t2:
	python main.py training2

py3t1:
	python3 main.py training1

py3t2:
	python3 main.py training2
