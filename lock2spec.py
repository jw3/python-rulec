#!/usr/bin/env python3

import shutil

import toml
import requests as req
from bs4 import BeautifulSoup

rawhide_rust = "https://mirrors.kernel.org/fedora/development/rawhide/Everything/source/tree/Packages/r/"
overridden_crates = ["paste", "indoc"]
blacklisted_crates = ["paste-impl", "indoc-impl", "parking_lot", "parking_lot_core"]


def required_packages():
    project_name = "example-rulec"
    with open('Cargo.lock') as lock:
        packages = toml.load(lock)["package"]
        required = {}
        for pkg in packages:
            name = pkg["name"]
            if name != project_name:
                version = pkg["version"]
                required[name] = version
        return required


def available_packages():
    soup = BeautifulSoup(req.get(rawhide_rust).text)
    links = soup.find_all('a')

    pkgs = {}
    for link in links:
        if link.text.startswith("rust-"):
            try:
                # rust-zstd-safe-4.1.4-2.fc37.src.rpm
                (name, version) = link.text.split("-", 1)[1].rsplit("-", 1)[0].rsplit("-", 1)
            except:
                continue

            pkgs[name] = version
    return pkgs


if __name__ == '__main__':
    rpms = {}
    crates = {}
    unvendor = []
    available = available_packages()
    for p, v in required_packages().items():
        if p in available:
            if v == available[p]:
                rpms[p] = f"rust-{p}"
                unvendor.append(p)
            else:
                print("rpm version didnt match")
                crates[p] = f"%{{crates_source {p} {v}}}"
        else:
            crates[p] = f"%{{crates_source {p} {v}}}"
        # Source1: %{crates_source lmdb-rkv 0.14.0}
        # print(f"Source{i+1}: %{{crates_source {p} {v}}}")

    print("BuildRequires:  rust-packaging")
    for r in rpms.values():
        print(f"BuildRequires: {r}-devel")

    if overridden_crates:
        print("# Overridden to rpms due to Fedora version patching")
        for r in overridden_crates:
            print(f"BuildRequires: rust-{r}-devel")
            unvendor.append(r)

    # if not vendoring
    excluded_crates = overridden_crates + blacklisted_crates
    for i, (c, v) in enumerate(crates.items()):
        if c not in excluded_crates:
            print(f"Source{i + 1 }: {v}")

    # if vendoring
    for c in unvendor:
        shutil.rmtree(f"vendor/{c}", ignore_errors=True)
