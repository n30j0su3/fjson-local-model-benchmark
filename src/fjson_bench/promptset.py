from dataclasses import dataclass
from pathlib import Path
import hashlib

@dataclass(frozen=True)
class PromptAsset:
    name: str
    text: str
    sha256: str


def load_prompt(path: Path) -> PromptAsset:
    path = Path(path)
    data = path.read_bytes()
    return PromptAsset(path.name, data.decode("utf-8"), hashlib.sha256(data).hexdigest())


def load_promptset(root: Path) -> dict[str, PromptAsset]:
    root = Path(root)
    assets = {path.name: load_prompt(path) for path in sorted(root.glob("*.txt"))}
    required = {"system.txt", "d1-visual-plan.txt", "d1-visual-build.txt", "d2-ecommerce-plan.txt", "d2-ecommerce-build.txt", "d3-threejs-plan.txt", "d3-threejs-build.txt", "repair.txt"}
    missing = required - set(assets)
    if missing:
        raise ValueError(f"missing prompts: {sorted(missing)}")
    return assets
