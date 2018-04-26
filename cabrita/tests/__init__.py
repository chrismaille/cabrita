

COMPOSE_YAML = \
    """
    version: "3"
    services:
      django:
        image: django:dev
        build:
          context: ${HOME}/Projects
        ports:
          - '8081:8080'
        environment:
          - DEBUG=true
        volumes:
          - ${HOME}/Projects:/opt/app
        networks:
          backend:
            aliases:
              - django
      django-worker:
        image: django:dev
        ports:
          - '8085:8080'
        build:
        depends_on:
          - django
        volumes:
          - ${HOME}/Projects:/opt/app
        networks:
          backend:
            aliases:
              - django-worker
      postgres:
        image: postgres:9.6
        volumes:
            - postgres-data:/var/lib/postgresql/data
        ports:
            - "5433:5432"
        networks:
          backend:
            aliases:
              - postgres
    volumes:
      postgres-data:
    networks:
      backend:
        driver: bridge
    """