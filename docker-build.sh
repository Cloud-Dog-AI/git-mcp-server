#!/usr/bin/env bash
# Copyright 2026 Cloud-Dog, Viewdeck Engineering Limited
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# git-mcp-server — Docker Build Script (PS-91 / PS-97 v1.1 §1.1.3)
# Uses BuildKit secret mount for optional package-index credentials; credentials never enter image layers.
#
# Variant selector (PS-97 v1.1 §1.1.3):
#   --variant public  (default) builds Dockerfile.public for publication
#   --variant dev     builds Dockerfile.dev when that file exists in a developer checkout
#
# Usage:
#   docker-build.sh [VERSION] [--variant dev|public]
#
# Env overrides still apply (PYPI_URL, CUSTOM_CA_CERT, etc.). The --variant flag
# selects which Dockerfile is fed to BuildKit.
set -euo pipefail

require_main_or_release_branch() {
  local branch
  branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
  # Publication-suffixed artifacts are local verification builds; the suffix
  # path suppresses registry tagging, so it is safe from a repair branch.
  if [[ -n "${PUBLICATION_TAG_SUFFIX:-}" ]]; then
    return 0
  fi
  case "${branch}" in
    main|release/*)
      return 0
      ;;
  esac

  echo "ERROR: docker-build.sh refuses to build/push from non-main branch. Got '${branch:-unknown}'; checkout main or release/*." >&2
  exit 1
}

require_main_or_release_branch

# ── Argument parsing ────────────────────────────────────────────
VARIANT="${PUBLICATION_BUILD_VARIANT:-public}"
POSITIONAL=()
while [[ $# -gt 0 ]]; do
  case "$1" in
    --variant)
      VARIANT="${2:-dev}"
      shift 2
      ;;
    --variant=*)
      VARIANT="${1#*=}"
      shift
      ;;
    *)
      POSITIONAL+=("$1")
      shift
      ;;
  esac
done
set -- "${POSITIONAL[@]}"

case "${VARIANT}" in
  dev|public) ;;
  *)
    echo "ERROR: --variant must be 'dev' or 'public' (got: ${VARIANT})" >&2
    exit 2
    ;;
esac

DOCKERFILE="Dockerfile.${VARIANT}"
if [[ ! -f "${DOCKERFILE}" ]]; then
  echo "ERROR: ${DOCKERFILE} not found (variant=${VARIANT})" >&2
  exit 2
fi

VERSION="${1:-latest}"
CONTAINER="git-mcp-server"
FOLDER="cloud-dog"
REGISTRY="${REGISTRY:-}"
PIP_CONF=".pip.conf.build"
PIP_NETRC=".pip.netrc.build"
CA_BUNDLE_FILE=".ca-bundle.build"
cleanup_build_secrets() {
  rm -f "${PIP_CONF}" "${PIP_NETRC}" "${CA_BUNDLE_FILE}"
}
trap cleanup_build_secrets EXIT

PUBLICATION_TAG_SUFFIX="${PUBLICATION_TAG_SUFFIX:-}"
if [[ -n "${PUBLICATION_TAG_SUFFIX}" ]]; then
  if [[ ! "${PUBLICATION_TAG_SUFFIX}" =~ ^[a-z0-9]([a-z0-9-]*[a-z0-9])?$ ]]; then
    echo "ERROR: PUBLICATION_TAG_SUFFIX must match ^[a-z0-9]([a-z0-9-]*[a-z0-9])?\$ (got: '${PUBLICATION_TAG_SUFFIX}')" >&2
    exit 2
  fi
  case "${PUBLICATION_TAG_SUFFIX}" in
    latest|dev|prod|release|stable)
      echo "ERROR: PUBLICATION_TAG_SUFFIX '${PUBLICATION_TAG_SUFFIX}' is reserved" >&2
      exit 2
      ;;
  esac
  EFFECTIVE_TAG="${VERSION}-${PUBLICATION_TAG_SUFFIX}"
  echo "Publication test build: tag suffix '-${PUBLICATION_TAG_SUFFIX}' (registry tag will be skipped)."
else
  EFFECTIVE_TAG="${VERSION}"
fi

# CA sources (any that exist will be merged in this order)
CUSTOM_CA_CERT="${CUSTOM_CA_CERT:-}"
CORPORATE_CA_CERT="${CORPORATE_CA_CERT:-/usr/local/share/ca-certificates/cloud-dog.net.ca.crt}"
ACME_CA_CERT="${ACME_CA_CERT:-}"

echo "=========================================="
echo "Docker Build: ${FOLDER}/${CONTAINER}:${EFFECTIVE_TAG} (variant=${VARIANT}, dockerfile=${DOCKERFILE})"
echo "=========================================="

# ── PyPI Configuration ───────────────────────────────────────────
# Public variant (PS-97 v1.1 §3.3 / §4): a SINGLE public index, default public
# PyPI, passed to the build as the PUBLIC_PYPI_INDEX_URL ARG. No internal index
# host, no --extra-index-url. Dev variant requires an explicit approved index.
if [[ "${VARIANT}" == "public" ]]; then
  # A caller-supplied PYPI_URL is the documented single-index override for
  # publication rehearsal builds.  Preserve the public default only when
  # neither explicit index variable is present.
  PUBLIC_PYPI_INDEX_URL="${PUBLIC_PYPI_INDEX_URL:-${PYPI_URL:-https://pypi.org/simple/}}"
  PYPI_URL="${PUBLIC_PYPI_INDEX_URL}"
  echo "Public package index: ${PUBLIC_PYPI_INDEX_URL}"
else
  PUBLIC_PYPI_INDEX_URL=""
  if [[ -z "${PYPI_URL:-}" ]]; then
    echo "ERROR: --variant dev requires an explicit PYPI_URL" >&2
    exit 2
  fi
fi
PYPI_USERNAME="${PYPI_USERNAME:-}"
PYPI_PASSWORD="${PYPI_PASSWORD:-}"
# Trusted host derived from the active index URL (no internal literal default).
PYPI_TRUSTED_HOST="$(python3 -c "from urllib.parse import urlsplit; print(urlsplit('${PYPI_URL}').hostname or 'pypi.org')")"

# Generate a credential-free pip.conf plus a BuildKit-secret netrc auth helper.
# Credentials never enter the index URL, build arguments, logs, or image layers.
cat > "${PIP_CONF}" << EOF
[global]
index-url = ${PYPI_URL}
trusted-host = ${PYPI_TRUSTED_HOST}
EOF
rm -f "${PIP_NETRC}"
touch "${PIP_NETRC}"
if [[ -n "${PYPI_USERNAME}" && -n "${PYPI_PASSWORD}" ]]; then
  printf 'machine %s\nlogin %s\npassword %s\n' \
    "${PYPI_TRUSTED_HOST}" "${PYPI_USERNAME}" "${PYPI_PASSWORD}" > "${PIP_NETRC}"
  echo "pip auth helper generated as a BuildKit secret (strict-single-index, PS-97 §3.5)."
elif [[ -n "${PYPI_USERNAME}" || -n "${PYPI_PASSWORD}" ]]; then
  echo "ERROR: PYPI_USERNAME and PYPI_PASSWORD must be provided together" >&2
  rm -f "${PIP_CONF}" "${PIP_NETRC}"
  exit 2
else
  echo "NOTE: No PyPI credentials set — using anonymous access."
fi
chmod 600 "${PIP_CONF}" "${PIP_NETRC}"

# ── CA Certificate ───────────────────────────────────────────────
rm -f "${CA_BUNDLE_FILE}"
touch "${CA_BUNDLE_FILE}"
for cert in "${CUSTOM_CA_CERT}" "${CORPORATE_CA_CERT}" "${ACME_CA_CERT}"; do
  if [[ -n "${cert}" && -f "${cert}" ]]; then
    cat "${cert}" >> "${CA_BUNDLE_FILE}"
    echo "" >> "${CA_BUNDLE_FILE}"
  fi
done
chmod 600 "${CA_BUNDLE_FILE}"

# ── Build ────────────────────────────────────────────────────────
# Public variant feeds the single public index to the Dockerfile via the
# PUBLIC_PYPI_INDEX_URL ARG. Dev variant supplies its index via PYPI_URL ARG.
PUBLIC_INDEX_BUILD_ARG=()
if [[ "${VARIANT}" == "public" ]]; then
  PUBLIC_INDEX_BUILD_ARG=(--build-arg PUBLIC_PYPI_INDEX_URL="${PUBLIC_PYPI_INDEX_URL}")
else
  PUBLIC_INDEX_BUILD_ARG=(--build-arg PYPI_URL="${PYPI_URL}")
fi

# ── W28C-1719 publish-before-pin guard + build-provenance revision label (fail-closed) ──
_PBP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
NETRC="${PIP_NETRC}" "${_PBP_DIR}/scripts/publish-before-pin-guard.sh" "${_PBP_DIR}" || exit $?
_PBP_REV="$(git -C "${_PBP_DIR}" rev-parse HEAD 2>/dev/null || echo unknown)"
# W28E-1863 fix-wave-d (WSC-014): propagate build identity to the image so the
# Dockerfile can stamp OCI labels + runtime ENV for _build_identity() / /ui/version.
SOURCE_COMMIT="${_PBP_REV}"
SOURCE_BRANCH="$(git -C "${_PBP_DIR}" rev-parse --abbrev-ref HEAD 2>/dev/null || echo unknown)"
BUILD_DATE="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# W28R-3014-R4 Cloud-Dog-only boundary: tag the dev image directly with the internal
# registry reference so BuildKit does not emit a `docker.io/<name>` default-namespace
# naming line (a registryless `-t` normalises to docker.io/... in the build log).
if [[ "${VARIANT}" == "dev" && -n "${REGISTRY}" && -z "${PUBLICATION_TAG_SUFFIX}" ]]; then
  IMAGE_REF="${REGISTRY}/${FOLDER}/${CONTAINER}:${EFFECTIVE_TAG}"
else
  IMAGE_REF="${FOLDER}/${CONTAINER}:${EFFECTIVE_TAG}"
fi

DOCKER_BUILDKIT=1 docker buildx build \
  --label "org.opencontainers.image.revision=${_PBP_REV}" \
  --progress=plain \
  --network=host \
  --load \
  -f "${DOCKERFILE}" \
  --secret id=pip_conf,src="${PIP_CONF}" \
  --secret id=pip_netrc,src="${PIP_NETRC}" \
  --secret id=ca_bundle,src="${CA_BUNDLE_FILE}" \
  "${PUBLIC_INDEX_BUILD_ARG[@]}" \
  --build-arg HTTP_PROXY="${HTTP_PROXY:-}" \
  --build-arg HTTPS_PROXY="${HTTPS_PROXY:-}" \
  --build-arg NO_PROXY="${NO_PROXY:-}" \
  --build-arg http_proxy="${http_proxy:-}" \
  --build-arg https_proxy="${https_proxy:-}" \
  --build-arg no_proxy="${no_proxy:-}" \
  --build-arg SOURCE_COMMIT="${SOURCE_COMMIT}" \
  --build-arg SOURCE_BRANCH="${SOURCE_BRANCH}" \
  --build-arg BUILD_DATE="${BUILD_DATE}" \
  -t "${IMAGE_REF}" \
  . 2>&1 | tee docker-build.log

BUILD_STATUS=${PIPESTATUS[0]}

if [[ ${BUILD_STATUS} -eq 0 ]]; then
  echo "Build OK: ${IMAGE_REF} (variant=${VARIANT})"
  if [[ "${VARIANT}" == "dev" && -n "${REGISTRY}" && -z "${PUBLICATION_TAG_SUFFIX}" ]]; then
    # Already built + tagged directly with the internal registry reference (IMAGE_REF).
    echo "Tagged: ${IMAGE_REF}"
  elif [[ -n "${PUBLICATION_TAG_SUFFIX}" ]]; then
    echo "Registry tag skipped for publication suffix '${PUBLICATION_TAG_SUFFIX}'."
  else
    echo "Public variant built; internal registry tag skipped (PS-97 §1.1.3 closed-loop)."
  fi
else
  echo "Build FAILED — see docker-build.log"
fi

# ── Cleanup secrets ──────────────────────────────────────────────
cleanup_build_secrets
exit ${BUILD_STATUS}
