#!/usr/bin/env python3
"""
Generate a CycloneDX SBOM (JSON) from Poetry files without network access.

Sources:
- pyproject.toml for app metadata
- poetry.lock for resolved dependencies

Usage:
  python tools/generate_sbom.py --output sbom.cdx.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import uuid
from datetime import datetime, timezone


def load_toml(path: str) -> dict:
    """Attempt to load TOML via tomllib; fallback to minimal custom parser for Poetry files."""
    try:
        import tomllib  # py311+
        with open(path, "rb") as f:
            return tomllib.load(f)
    except Exception:
        # Fallbacks
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        if os.path.basename(path) == "pyproject.toml":
            return parse_pyproject_min(text)
        if os.path.basename(path) == "poetry.lock":
            return parse_poetry_lock_min(text)
        raise


def parse_pyproject_min(text: str) -> dict:
    """Minimal parser to extract tool.poetry.name and version."""
    name = None
    version = None
    in_tool_poetry = False
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            in_tool_poetry = (line == "[tool.poetry]")
            continue
        if in_tool_poetry:
            if line.startswith("name =") and name is None:
                name = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("version =") and version is None:
                version = line.split("=", 1)[1].strip().strip('"')
            if name and version:
                break
    return {"tool": {"poetry": {"name": name or "application", "version": version or "0.0.0"}}}


def parse_poetry_lock_min(text: str) -> dict:
    """Minimal parser for Poetry 2 lock format to extract packages, files, dependencies."""
    packages = []
    cur = None
    section = None  # None | "package" | "deps"
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "[[package]]":
            if cur:
                packages.append(cur)
            cur = {"name": None, "version": None, "license": None, "files": [], "dependencies": {}}
            section = "package"
            continue
        if line.startswith("[package."):
            if line.startswith("[package.dependencies]"):
                section = "deps"
            else:
                section = None
            continue
        if cur is None:
            continue
        # parse key = value
        if section == "package":
            if line.startswith("name ="):
                cur["name"] = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("version ="):
                cur["version"] = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("license ="):
                cur["license"] = line.split("=", 1)[1].strip().strip('"')
            elif line.startswith("files = ["):
                # collect until closing ]
                files = []
                if line.endswith("]") and line != "files = []":
                    # single-line array; still parse
                    pass
                else:
                    # consume subsequent lines
                    continue
            elif line.startswith("") and line.startswith("{file ="):
                # Not reliable in minimal parser; skip
                pass
        if section == "deps":
            # format: name = "version spec" OR name = { ... }
            if "=" in line and not line.startswith("["):
                dep_name = line.split("=", 1)[0].strip()
                cur["dependencies"][dep_name] = True
    if cur:
        packages.append(cur)
    return {"package": packages}


def make_purl(name: str, version: str) -> str:
    # PyPI purl spec
    return f"pkg:pypi/{name.lower()}@{version}"


def build_components_and_deps(lock: dict) -> tuple[list[dict], list[dict]]:
    """Build CycloneDX components[] and dependencies[] from poetry.lock TOML."""
    pkgs = lock.get("package") or []
    # name->version for lookup
    nv = {p.get("name"): p.get("version") for p in pkgs}

    components: list[dict] = []
    deps: list[dict] = []

    for p in pkgs:
        name = p.get("name")
        version = p.get("version")
        if not (name and version):
            continue
        purl = make_purl(name, version)
        comp = {
            "bom-ref": purl,
            "type": "library",
            "name": name,
            "version": version,
            "purl": purl,
        }
        if p.get("license"):
            comp["licenses"] = [{"license": {"id": p.get("license")}}]
        # Attach hashes if present
        files = p.get("files") or []
        hashes = []
        for f in files:
            h = f.get("hash")
            if h and h.startswith("sha256:"):
                hashes.append({"alg": "SHA-256", "content": h.split(":", 1)[1]})
        if hashes:
            comp["hashes"] = hashes

        components.append(comp)

        # Dependencies mapping
        deps_raw = p.get("dependencies") or {}
        depends_on = []
        for dep_name in deps_raw.keys():
            ver = nv.get(dep_name)
            if ver:
                depends_on.append(make_purl(dep_name, ver))
        if depends_on:
            deps.append({"ref": purl, "dependsOn": depends_on})

    return components, deps


def sanitize_spdx_id(text: str) -> str:
    import re
    return re.sub(r"[^A-Za-z0-9\-\.]+", "-", text)[:100]


def build_spdx(pyproject: dict, lock: dict) -> dict:
    tool = pyproject.get("tool", {})
    poetry = tool.get("poetry", {})
    app_name = poetry.get("name", "application")
    app_version = poetry.get("version", "0.0.0")
    doc_ns = f"urn:uuid:{uuid.uuid4()}"
    created = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    pkgs = lock.get("package") or []
    spdx_packages = []
    for p in pkgs:
        name = p.get("name")
        version = p.get("version")
        if not (name and version):
            continue
        spdxid = f"SPDXRef-PACKAGE-{sanitize_spdx_id(name)}"
        pkg = {
            "SPDXID": spdxid,
            "name": name,
            "versionInfo": version,
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False,
            "externalRefs": [
                {
                    "referenceCategory": "PACKAGE-MANAGER",
                    "referenceType": "purl",
                    "referenceLocator": make_purl(name, version),
                }
            ],
        }
        if p.get("license"):
            lic = p.get("license")
            pkg["licenseConcluded"] = lic
            pkg["licenseDeclared"] = lic
        spdx_packages.append(pkg)

    spdx_doc = {
        "spdxVersion": "SPDX-2.3",
        "dataLicense": "CC0-1.0",
        "SPDXID": "SPDXRef-DOCUMENT",
        "name": f"{app_name}-sbom",
        "documentNamespace": doc_ns,
        "creationInfo": {
            "created": created,
            "creators": [
                "Tool: generate_sbom.py-1.0.0"
            ],
        },
        "documentDescribes": [
            f"SPDXRef-PACKAGE-{sanitize_spdx_id(app_name)}"
        ],
        "packages": [
            {
                "SPDXID": f"SPDXRef-PACKAGE-{sanitize_spdx_id(app_name)}",
                "name": app_name,
                "versionInfo": app_version,
                "downloadLocation": "NOASSERTION",
                "filesAnalyzed": False,
            }
        ] + spdx_packages,
    }
    return spdx_doc


def build_bom(pyproject: dict, lock: dict) -> dict:
    tool = pyproject.get("tool", {})
    poetry = tool.get("poetry", {})
    app_name = poetry.get("name", "application")
    app_version = poetry.get("version", "0.0.0")

    components, dep_rels = build_components_and_deps(lock)
    app_ref = f"urn:uuid:{uuid.uuid4()}"

    bom = {
        "bomFormat": "CycloneDX",
        "specVersion": "1.4",
        "version": 1,
        "serialNumber": f"urn:uuid:{uuid.uuid4()}",
        "metadata": {
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "tools": [
                {
                    "vendor": "custom",
                    "name": "generate_sbom.py",
                    "version": "1.0.0",
                }
            ],
            "component": {
                "bom-ref": app_ref,
                "type": "application",
                "name": app_name,
                "version": app_version,
            },
        },
        "components": components,
    }
    if dep_rels:
        bom["dependencies"] = dep_rels
    return bom


def write_csv(components: list[dict], out_path: str) -> None:
    import csv
    fields = ["name", "version", "purl", "type", "bom-ref", "hashes"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for c in components:
            hashes = c.get("hashes") or []
            hashes_str = ";".join([f"{h.get('alg')}={h.get('content')}" for h in hashes]) if hashes else ""
            w.writerow({
                "name": c.get("name", ""),
                "version": c.get("version", ""),
                "purl": c.get("purl", ""),
                "type": c.get("type", ""),
                "bom-ref": c.get("bom-ref", ""),
                "hashes": hashes_str,
            })


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate CycloneDX SBOM from Poetry files")
    ap.add_argument("--pyproject", default="pyproject.toml", help="Path to pyproject.toml")
    ap.add_argument("--lockfile", default="poetry.lock", help="Path to poetry.lock")
    ap.add_argument("--output", default="sbom.cdx.json", help="CycloneDX JSON output file path")
    ap.add_argument("--csv-output", default="sbom.csv", help="CSV output file path")
    ap.add_argument("--spdx-output", default="sbom.spdx.json", help="SPDX JSON output file path")
    args = ap.parse_args()

    if not os.path.exists(args.pyproject):
        print(f"Error: {args.pyproject} not found", file=sys.stderr)
        return 2
    if not os.path.exists(args.lockfile):
        print(f"Error: {args.lockfile} not found", file=sys.stderr)
        return 2

    pyproject = load_toml(args.pyproject)
    lock = load_toml(args.lockfile)
    bom = build_bom(pyproject, lock)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(bom, f, indent=2, sort_keys=False)
    print(f"Wrote {args.output} ({len(bom.get('components', []))} components)")

    # Also write CSV summary
    try:
        write_csv(bom.get("components", []), args.csv_output)
        print(f"Wrote {args.csv_output}")
    except Exception as e:
        print(f"Warning: failed to write CSV: {e}", file=sys.stderr)

    # Write SPDX JSON
    try:
        spdx = build_spdx(pyproject, lock)
        with open(args.spdx_output, "w", encoding="utf-8") as f:
            json.dump(spdx, f, indent=2)
        print(f"Wrote {args.spdx_output}")
    except Exception as e:
        print(f"Warning: failed to write SPDX: {e}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
