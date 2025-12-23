# Makefile pour le projet legal230-latest
# Permet d'exécuter les commandes depuis lara ou legal230-latest

# ============================================================================
# Configuration
# ============================================================================
LARA_DIR := /home/ubuntu/lara
LEGAL_DIR := /home/ubuntu/legal230-latest
ACTION := $(filter-out lara-bridge lexa all,$(MAKECMDGOALS))

# Configuration Docker Compose pour lexa
DOCKER_COMPOSE_LEXA := docker-compose -f docker-compose.prod.yaml

# ============================================================================
# Cible par défaut
# ============================================================================
.DEFAULT_GOAL := help

help:
	@echo "Usage: make [lara-bridge|lexa|all] [restart|build|static|makemigrations|migrate|compile-messages|compile messages]"
	@echo ""
	@echo "Exemples:"
	@echo "  make lara-bridge restart"
	@echo "  make lara-bridge build"
	@echo "  make lexa restart"
	@echo "  make lexa build"
	@echo "  make lexa static"
	@echo "  make lexa makemigrations"
	@echo "  make lexa migrate"
	@echo "  make lexa compile-messages"
	@echo "  make lexa compile messages"
	@echo "  make all restart"
	@echo "  make all build"
	@echo "  make all static"

# ============================================================================
# Actions pour lara-bridge - délègue au Makefile de lara
# ============================================================================
lara-bridge:
	@$(MAKE) -C $(LARA_DIR) $(MAKECMDGOALS)

# ============================================================================
# Actions pour lexa
# ============================================================================
lexa:
	@if [ -z "$(ACTION)" ]; then \
		echo "Action requise. Exemple: make lexa restart"; \
		exit 1; \
	fi
	@ACTION_JOINED=$$(echo "$(ACTION)" | tr ' ' '-'); \
	case "$$ACTION_JOINED" in \
		restart) \
			echo "[lexa] Redémarrage du service runserver..."; \
			cd $(LEGAL_DIR) && $(DOCKER_COMPOSE_LEXA) restart runserver ;; \
		build) \
			echo "[lexa] Build et démarrage du service runserver..."; \
			cd $(LEGAL_DIR) && $(DOCKER_COMPOSE_LEXA) up -d --build runserver ;; \
		static) \
			echo "[lexa] Collecte des fichiers statiques..."; \
			cd $(LEGAL_DIR) && $(DOCKER_COMPOSE_LEXA) exec runserver python manage.py collectstatic --noinput ;; \
		makemigrations) \
			echo "[lexa] Création des migrations..."; \
			cd $(LEGAL_DIR) && $(DOCKER_COMPOSE_LEXA) exec runserver python manage.py makemigrations ;; \
		migrate) \
			echo "[lexa] Application des migrations..."; \
			cd $(LEGAL_DIR) && $(DOCKER_COMPOSE_LEXA) exec runserver python manage.py migrate ;; \
		compile-messages|compilemessages) \
			echo "[lexa] Compilation des messages de traduction..."; \
			cd $(LEGAL_DIR) && python3 manage.py compilemessages && \
			echo "[lexa] Redémarrage du service après compilation..."; \
			$(MAKE) lexa ACTION=restart ;; \
		*) \
			echo "Action '$(ACTION)' non supportée pour lexa" ;; \
	esac

# ============================================================================
# Actions pour tous les projets
# ============================================================================
all:
	@if [ -z "$(ACTION)" ]; then \
		echo "Action requise. Exemple: make all restart"; \
		exit 1; \
	fi
	@$(MAKE) -C $(LARA_DIR) lara-bridge $(ACTION)
	@$(MAKE) lexa $(ACTION)

# ============================================================================
# Règles génériques
# ============================================================================
# Empêche make de traiter les actions comme des cibles
%:
	@:
