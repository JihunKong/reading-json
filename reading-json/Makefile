.PHONY: build gen-para gen-art grade-sample clean

build:
	docker compose build

gen-para:
	docker compose run --rm generator python cli.py generate --count 5 --mode paragraph

gen-art:
	docker compose run --rm generator python cli.py generate --count 3 --mode article

grade-sample:
	docker compose run --rm grader python cli.py grade-sample --input grader/samples/submissions.csv

clean:
	rm -rf generator/out/* grader/reports/*
