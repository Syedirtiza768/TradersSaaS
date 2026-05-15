# Backend Dockerfile — Frappe + ERPNext + Trader App
# Optimized for faster iterative rebuilds while remaining compatible with the
# current docker-compose stack.

ARG FRAPPE_VERSION=version-15
ARG ERPNEXT_VERSION=version-15
ARG PYTHON_VERSION=python3.11

FROM frappe/bench:latest AS base

ARG FRAPPE_VERSION
ARG ERPNEXT_VERSION
ARG PYTHON_VERSION

USER frappe
WORKDIR /home/frappe

# Bench + ERPNext are the expensive layers. Keep them ahead of app source copies
# so app-only changes can reuse these layers during normal rebuilds.
RUN bench init \
    --frappe-branch ${FRAPPE_VERSION} \
    --skip-assets \
    --skip-redis-config-generation \
    --python ${PYTHON_VERSION} \
    /home/frappe/frappe-bench

WORKDIR /home/frappe/frappe-bench

RUN bench get-app --branch ${ERPNEXT_VERSION} erpnext

# Copy only dependency metadata first where possible so pip install can stay
# cached until app packaging/dependency files change.
COPY --chown=frappe:frappe apps/trader_app/pyproject.toml /home/frappe/frappe-bench/apps/trader_app/pyproject.toml
COPY --chown=frappe:frappe apps/trader_app/setup.py /home/frappe/frappe-bench/apps/trader_app/setup.py
COPY --chown=frappe:frappe apps/trader_app/setup.cfg /home/frappe/frappe-bench/apps/trader_app/setup.cfg
COPY --chown=frappe:frappe apps/trader_app/MANIFEST.in /home/frappe/frappe-bench/apps/trader_app/MANIFEST.in
COPY --chown=frappe:frappe apps/trader_app/requirements.txt /home/frappe/frappe-bench/apps/trader_app/requirements.txt

# Copy the full app source after metadata so code-only edits avoid invalidating
# the costly bench/ERPNext layers and only rebuild the final install layer.
COPY --chown=frappe:frappe apps/trader_app /home/frappe/frappe-bench/apps/trader_app

# bench get-app updates sites/apps.txt; trader_app is copied in manually, so register it.
RUN /home/frappe/frappe-bench/env/bin/pip install --no-cache-dir -e /home/frappe/frappe-bench/apps/trader_app \
    && printf '%s\n' frappe erpnext trader_app > sites/apps.txt

EXPOSE 8000 9000

CMD ["bench", "start"]
