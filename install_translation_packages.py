"""Install local English/Spanish Argos Translate packages."""

from __future__ import annotations

from argostranslate import package


LANGUAGE_PAIRS = [("en", "es"), ("es", "en")]


def main() -> None:
    print("Refreshing Argos package list...")
    package.update_package_index()
    available_packages = package.get_available_packages()

    for source, target in LANGUAGE_PAIRS:
        selected = next(
            (
                pkg
                for pkg in available_packages
                if pkg.from_code == source and pkg.to_code == target
            ),
            None,
        )

        if selected is None:
            print(f"No package found for {source}->{target}.")
            continue

        print(f"Downloading {source}->{target}...")
        path = selected.download()
        print(f"Installing {source}->{target}...")
        package.install_from_path(path)

    print("Done. Restart the live app after this finishes.")


if __name__ == "__main__":
    main()
