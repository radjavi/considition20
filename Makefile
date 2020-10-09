all: t1 t2

t1:
	python main.py training1 True

t2:
	python main.py training2 True

py3t1:
	python3 main.py training1 True

py3t2:
	python3 main.py training2 True

py3c1:
	python3 main.py Gothenburg True

py3c2:
	python3 main.py Kiruna True

py3c3:
	python3 main.py Visby True

py3c4:
	python3 main.py London True
