from typing import List, Optional


class AppManifest:
    """Represent application manifest
    """

    manifest: dict  # the manifest of the application

    def __init__(self, manifest: dict):
        self.manifest = manifest

    @property
    def version(self) -> str:
        return self.manifest["version"]

    @property
    def exclude_dirs(self) -> List[str]:
        return self.manifest.get("exclude_dirs", [])

    @property
    def on_stage(self) -> Optional[str]:
        return self.manifest.get("on_stage")

    def to_json(self) -> dict:
        return {
            "on_stage": self.on_stage,
            "version": self.version,
            "exclude_dirs": self.exclude_dirs
        }
