# Root Makefile - delegates to configs/Makefile
# This provides backward compatibility for make commands

%:
	$(MAKE) -f configs/Makefile $@

.PHONY: help
help:
	$(MAKE) -f configs/Makefile help