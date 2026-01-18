"""
Adapter Manager - Version Management for LoRA Adapters

Handles adapter versioning, storage, and lifecycle management.

Features:
- Semantic versioning for adapters
- Adapter registry with metadata
- Version comparison and rollback
- Adapter loading utilities
"""

import json
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional

import structlog
import yaml

from .config import DEFAULT_ADAPTERS_DIR

logger = structlog.get_logger()


@dataclass
class AdapterInfo:
    """Information about a trained adapter"""
    role: str
    version: str
    base_model: str
    created_at: datetime
    path: Path
    metrics: dict
    lora_config: dict
    is_latest: bool = False

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "version": self.version,
            "base_model": self.base_model,
            "created_at": self.created_at.isoformat(),
            "path": str(self.path),
            "metrics": self.metrics,
            "lora_config": self.lora_config,
            "is_latest": self.is_latest
        }


class AdapterManager:
    """
    Manages LoRA adapter versions and lifecycle

    Provides:
    - Version listing and comparison
    - Adapter loading for inference
    - Rollback to previous versions
    - Cleanup of old versions
    """

    def __init__(self, adapters_dir: Path = DEFAULT_ADAPTERS_DIR):
        self.adapters_dir = Path(adapters_dir)
        self.registry_path = self.adapters_dir / "adapter_registry.yaml"
        self._ensure_directory()

    def _ensure_directory(self):
        """Ensure adapters directory exists"""
        self.adapters_dir.mkdir(parents=True, exist_ok=True)

    def list_roles(self) -> list[str]:
        """List all roles with trained adapters"""
        roles = []
        for path in self.adapters_dir.iterdir():
            if path.is_dir() and not path.name.startswith("."):
                # Check if it has valid adapter versions
                if any(self._is_valid_adapter(p) for p in path.iterdir() if p.is_dir()):
                    roles.append(path.name)
        return sorted(roles)

    def list_versions(self, role: str) -> list[AdapterInfo]:
        """List all versions for a role"""
        role_dir = self.adapters_dir / role
        if not role_dir.exists():
            return []

        versions = []
        latest_version = self._get_latest_version(role)

        for version_dir in sorted(role_dir.iterdir(), reverse=True):
            if version_dir.is_dir() and self._is_valid_adapter(version_dir):
                if version_dir.name == "latest" or version_dir.is_symlink():
                    continue

                info = self._load_adapter_info(role, version_dir)
                if info:
                    info.is_latest = (version_dir.name == latest_version)
                    versions.append(info)

        return versions

    def _is_valid_adapter(self, path: Path) -> bool:
        """Check if path contains valid adapter files"""
        if path.is_symlink():
            return False

        required_files = ["adapter_config.json"]
        adapter_files = ["adapter_model.safetensors", "adapter_model.bin"]

        has_config = any((path / f).exists() for f in required_files)
        has_weights = any((path / f).exists() for f in adapter_files)

        return has_config and has_weights

    def _load_adapter_info(self, role: str, version_dir: Path) -> Optional[AdapterInfo]:
        """Load adapter information from metadata file"""
        metadata_path = version_dir / "training_metadata.json"

        if not metadata_path.exists():
            # Try to construct from available info
            config_path = version_dir / "adapter_config.json"
            if config_path.exists():
                with open(config_path) as f:
                    config = json.load(f)

                return AdapterInfo(
                    role=role,
                    version=version_dir.name,
                    base_model=config.get("base_model_name_or_path", "unknown"),
                    created_at=datetime.fromtimestamp(version_dir.stat().st_mtime),
                    path=version_dir,
                    metrics={},
                    lora_config=config
                )
            return None

        with open(metadata_path) as f:
            metadata = json.load(f)

        return AdapterInfo(
            role=role,
            version=metadata.get("version", version_dir.name),
            base_model=metadata.get("base_model", "unknown"),
            created_at=datetime.fromisoformat(metadata.get("created_at", datetime.now().isoformat())),
            path=version_dir,
            metrics=metadata.get("metrics", {}),
            lora_config=metadata.get("lora_config", {})
        )

    def _get_latest_version(self, role: str) -> Optional[str]:
        """Get the latest version name for a role"""
        latest_link = self.adapters_dir / role / "latest"
        if latest_link.is_symlink():
            return latest_link.resolve().name
        return None

    def get_adapter_path(
        self,
        role: str,
        version: str = "latest"
    ) -> Optional[Path]:
        """
        Get path to adapter for loading

        Args:
            role: Role name
            version: Version string or "latest"

        Returns:
            Path to adapter directory
        """
        if version == "latest":
            latest_link = self.adapters_dir / role / "latest"
            if latest_link.exists():
                return latest_link.resolve()
            # Fall back to most recent version
            versions = self.list_versions(role)
            if versions:
                return versions[0].path
            return None

        version_path = self.adapters_dir / role / version
        if version_path.exists() and self._is_valid_adapter(version_path):
            return version_path

        return None

    def set_latest(self, role: str, version: str) -> bool:
        """
        Set a specific version as latest

        Args:
            role: Role name
            version: Version to set as latest

        Returns:
            True if successful
        """
        version_path = self.adapters_dir / role / version
        if not version_path.exists() or not self._is_valid_adapter(version_path):
            logger.error("invalid_version", role=role, version=version)
            return False

        latest_link = self.adapters_dir / role / "latest"

        # Remove existing symlink
        if latest_link.exists() or latest_link.is_symlink():
            latest_link.unlink()

        # Create new symlink
        latest_link.symlink_to(version)

        logger.info("latest_updated", role=role, version=version)
        self._update_registry()

        return True

    def delete_version(self, role: str, version: str) -> bool:
        """
        Delete a specific adapter version

        Args:
            role: Role name
            version: Version to delete

        Returns:
            True if successful
        """
        if version == "latest":
            logger.error("cannot_delete_latest")
            return False

        version_path = self.adapters_dir / role / version

        if not version_path.exists():
            logger.warning("version_not_found", role=role, version=version)
            return False

        # Check if this is the latest
        latest_version = self._get_latest_version(role)
        if version == latest_version:
            logger.error("cannot_delete_active_latest", role=role, version=version)
            return False

        # Delete directory
        shutil.rmtree(version_path)
        logger.info("version_deleted", role=role, version=version)

        self._update_registry()
        return True

    def cleanup_old_versions(
        self,
        role: str,
        keep_count: int = 3
    ) -> list[str]:
        """
        Remove old versions, keeping only the most recent

        Args:
            role: Role name
            keep_count: Number of versions to keep

        Returns:
            List of deleted version names
        """
        versions = self.list_versions(role)

        if len(versions) <= keep_count:
            return []

        to_delete = versions[keep_count:]
        deleted = []

        for version_info in to_delete:
            if self.delete_version(role, version_info.version):
                deleted.append(version_info.version)

        return deleted

    def _update_registry(self):
        """Update the adapter registry file"""
        registry = {
            "updated_at": datetime.now().isoformat(),
            "roles": {}
        }

        for role in self.list_roles():
            versions = self.list_versions(role)
            latest = self._get_latest_version(role)

            registry["roles"][role] = {
                "latest": latest,
                "version_count": len(versions),
                "versions": [
                    {
                        "version": v.version,
                        "created_at": v.created_at.isoformat(),
                        "metrics": v.metrics.get("train_loss", "N/A")
                    }
                    for v in versions
                ]
            }

        with open(self.registry_path, "w") as f:
            yaml.dump(registry, f, default_flow_style=False)

    def get_registry(self) -> dict:
        """Load the adapter registry"""
        if self.registry_path.exists():
            with open(self.registry_path) as f:
                return yaml.safe_load(f)
        return {}

    def has_adapter(self, role: str) -> bool:
        """Check if an adapter exists for a role"""
        return self.get_adapter_path(role) is not None

    def compare_versions(
        self,
        role: str,
        version1: str,
        version2: str
    ) -> dict:
        """
        Compare two adapter versions

        Args:
            role: Role name
            version1: First version
            version2: Second version

        Returns:
            Comparison dictionary
        """
        info1 = None
        info2 = None

        for v in self.list_versions(role):
            if v.version == version1:
                info1 = v
            if v.version == version2:
                info2 = v

        if not info1 or not info2:
            return {"error": "One or both versions not found"}

        return {
            "version1": {
                "version": version1,
                "created_at": info1.created_at.isoformat(),
                "train_loss": info1.metrics.get("train_loss"),
                "eval_loss": info1.metrics.get("eval_loss"),
            },
            "version2": {
                "version": version2,
                "created_at": info2.created_at.isoformat(),
                "train_loss": info2.metrics.get("train_loss"),
                "eval_loss": info2.metrics.get("eval_loss"),
            },
            "improvement": {
                "train_loss": (
                    info1.metrics.get("train_loss", 0) - info2.metrics.get("train_loss", 0)
                    if info1.metrics.get("train_loss") and info2.metrics.get("train_loss")
                    else None
                ),
            }
        }

    def export_adapter(
        self,
        role: str,
        version: str,
        output_path: Path
    ) -> bool:
        """
        Export adapter to a portable archive

        Args:
            role: Role name
            version: Version to export
            output_path: Output path for archive

        Returns:
            True if successful
        """
        adapter_path = self.get_adapter_path(role, version)
        if not adapter_path:
            return False

        output_path = Path(output_path)
        shutil.make_archive(
            str(output_path.with_suffix("")),
            "zip",
            adapter_path
        )

        logger.info("adapter_exported", role=role, version=version, path=str(output_path))
        return True

    def import_adapter(
        self,
        archive_path: Path,
        role: str,
        version: str | None = None
    ) -> bool:
        """
        Import adapter from archive

        Args:
            archive_path: Path to adapter archive
            role: Role name to import as
            version: Version name (auto-generated if None)

        Returns:
            True if successful
        """
        archive_path = Path(archive_path)
        if not archive_path.exists():
            return False

        if version is None:
            version = f"imported_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        target_dir = self.adapters_dir / role / version
        target_dir.mkdir(parents=True, exist_ok=True)

        shutil.unpack_archive(str(archive_path), str(target_dir))

        if self._is_valid_adapter(target_dir):
            logger.info("adapter_imported", role=role, version=version)
            self._update_registry()
            return True
        else:
            shutil.rmtree(target_dir)
            return False


def get_manager(adapters_dir: Path | None = None) -> AdapterManager:
    """Get adapter manager instance"""
    if adapters_dir:
        return AdapterManager(adapters_dir)
    return AdapterManager()
