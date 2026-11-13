# GitHub Pages — landing pública Hydrosphere

## Propósito

Sitio estático en este repo (público):

- `/` — descarga escritorio (y móvil cuando exista)
- `/auth/callback` — puente post-OAuth de Supabase Auth

Fuente de verdad del contrato Auth/host: repo privado Hydrosphere → `docs/architecture/supabase-auth-url-hosting-v1.md`.

## Activar Pages

1. Repo **Hydrosphere-Distribution** → **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: `main` → carpeta `/docs` → Save

URL prevista:

`https://hydrosphereennde.github.io/Hydrosphere-Distribution/`

## Reglas

- Solo HTML/CSS/JS estático.
- Sin secretos, sin código de producto, sin API keys.
- El enlace de descarga de escritorio debe apuntar a un asset de GitHub Releases de este repo.
