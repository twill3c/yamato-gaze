# yamato-gaze — bronze 取得は手動実行のみ(N-02)
.PHONY: bronze test

bronze:
	python -m extract.aozora fetch

test:
	python -m pytest -q --tb=no
