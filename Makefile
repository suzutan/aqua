.PHONY: all

dev:
	python dev.py
start:
	python app.py

backup:
	cat config/development.yaml | gopass insert -f suzutan/app/aqua/development.yaml
	cat config/production.yaml | gopass insert -f suzutan/app/aqua/production.yaml
	cat settings.yaml | gopass insert -f suzutan/app/aqua/settings.yaml
	cat credentials.json | gopass insert -f suzutan/app/aqua/credentials.json
	gopass sync

restore:
	gopass sync
	gopass show suzutan/app/aqua/development.yaml > config/development.yaml
	gopass show suzutan/app/aqua/production.yaml > config/production.yaml
	gopass show suzutan/app/aqua/settings.yaml > settings.yaml
	gopass show suzutan/app/aqua/credentials.json > credentials.json
build:
	docker build -t aqua .

run-prod: build
	docker run --rm --name aqua \
	-e APP_ENV=production \
	-v ${PWD}/settings.yaml:/app/settings.yaml \
	-v ${PWD}/credentials.json:/app/credentials.json \
	-v ${PWD}/config/production.yaml:/app/config/production.yaml \
	aqua
