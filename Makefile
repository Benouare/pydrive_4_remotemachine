init:
	pip install -r requirements.txt

test:
	rm -rf tests/google_drive
	rm -rf tests/settings.yaml
	pytest -x -v tests/ -s


test-coverage:
	rm -rf tests/google_drive
	rm -rf tests/settings.yaml
	pytest --cov=pydrivesync --cov-report=html -v tests/
	open htmlcov/index.html

lib-lint:
		flake8 --ignore=W504 --max-line-length=127 --max-complexity=19 pydrivesync/ tests/ setup.py
		mypy --strict --ignore-missing-imports pynas/ tests/ setup.py

test-local:
	python test-local.py


lib-clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	rm -f .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build
	rm -rf proxy.py.egg-info
	rm -rf .pytest_cache
	rm -rf .mypy_cache
	rm -rf .hypothesis

package:lib-clean
	python setup.py bdist_wheel

deploy:
	cp dist/pydrivesync*.whl ../nas_install/
