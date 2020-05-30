.PHONY: all

dev:
	pipenv run dev
start:
	pipenv run start

backup:
	cat config/development.yaml | gopass insert -f suzutan/app/aqua/development.yaml
	cat settings.yaml | gopass insert -f suzutan/app/aqua/settings.yaml
	cat credentials.json | gopass insert -f suzutan/app/aqua/credentials.json
	gopass sync

restore:
	gopass sync
	gopass show suzutan/app/aqua/development.yaml > config/development.yaml
	gopass show suzutan/app/aqua/settings.yaml > settings.yaml
	gopass show suzutan/app/aqua/credentials.json > credentials.json
