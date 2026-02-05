.PHONY: ping-spam

HOST ?= https://localhost/
PINGSERVER_DIR = pingserver

ping-spam:
	uv run locust -f $(PINGSERVER_DIR) \
	-T ping-traffic \
	--config $(PINGSERVER_DIR)/pyproject.toml \
	--host $(HOST)
