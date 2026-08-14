# Hydrosphere

> Software profesional para preparar, analizar y documentar inspecciones de tuberías.

<!-- RELEASE:START -->
[![Descargar Hydrosphere para Windows](https://img.shields.io/badge/Descargar-Hydrosphere%20para%20Windows-0B5CAB?style=for-the-badge&logo=windows&logoColor=white)](https://github.com/HydrosphereEnnde/Hydrosphere-Distribution/releases/download/v0.0.4/Hydrosphere-0.0.4-win-x86_64-per-user.exe)

## Descarga la última versión

| Versión | Publicada | Instalador | Tamaño |
| --- | --- | --- | --- |
| 0.0.4 | 14 de agosto de 2026 | Windows 64 bits | 201 MB |

[Descargar Hydrosphere 0.0.4 para Windows](https://github.com/HydrosphereEnnde/Hydrosphere-Distribution/releases/download/v0.0.4/Hydrosphere-0.0.4-win-x86_64-per-user.exe)

SHA-256: `2c7b0761161e7e37a7591d99e5e4d5d88ed9de8a383f905a453bdb291d1d5489`

[Ver notas de la versión](https://github.com/HydrosphereEnnde/Hydrosphere-Distribution/releases/tag/v0.0.4) · [Ver todas las versiones](https://github.com/HydrosphereEnnde/Hydrosphere-Distribution/releases)
<!-- RELEASE:END -->

## Instalación

1. Descarga el instalador para Windows.
2. Abre el archivo `.exe`.
3. Sigue el asistente de instalación.

> El instalador actual todavía no está firmado con un certificado comercial Authenticode. Windows puede mostrar un aviso de editor desconocido o SmartScreen. Esto no impide la instalación; verifica que la descarga procede de esta página oficial y, si lo deseas, compara el SHA-256 publicado. No se trata de un error del instalador ni de un aviso de Control de cuentas de usuario (UAC).

Uso de los binarios oficiales: se requiere una licencia válida de Hydrosphere.

[Repositorio principal de Hydrosphere](https://github.com/HydrosphereEnnde/Hydrosphere)

## Documentación técnica de distribución

Este repositorio publica los activos oficiales de Hydrosphere: instaladores para Windows, el manifiesto de actualización firmado y los metadatos de cada release.

> **Código fuente:** este repositorio no contiene el código de la aplicación. El desarrollo se mantiene en el repositorio principal de Hydrosphere.

### Reglas de uso

* **Sin desarrollo aquí:** no envíe cambios de lógica de la aplicación a este repositorio.
* **Sin secretos:** no publique claves privadas, certificados, archivos de entorno ni credenciales.
* **Canal estable:** las versiones estables se publican como GitHub Releases. Los canales `beta` e `internal` se marcan como prerelease y no actualizan el bloque de descarga de esta página.

### Autenticidad

GitHub es el medio de transporte y almacenamiento; no es la autoridad criptográfica.

1. **Manifiesto Ed25519:** `hydrosphere-update-manifest-v1.json` incluye metadatos y hashes, firmado con la clave de actualización.
2. **Integridad SHA-256:** el checksum del instalador debe coincidir con el hash del manifiesto (y con el publicado en esta página).
3. **Authenticode:** la infraestructura de firma está lista; el certificado comercial sigue pendiente, por eso Windows puede mostrar editor desconocido o SmartScreen.
4. **Validación fail-closed:** la aplicación valida de forma estricta manifiestos y binarios descargados.

El diseño previsto de nombres y manifiesto está en [docs/release-layout.md](docs/release-layout.md). La política de seguridad está en [SECURITY.md](SECURITY.md).
