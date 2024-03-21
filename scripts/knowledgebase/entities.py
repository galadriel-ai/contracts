from dataclasses import dataclass


@dataclass(frozen=True)
class Metadata:
    source: str

    def to_dict(self):
        return {
            "source": self.source,
        }


@dataclass(frozen=True)
class CollectionObject:
    id: str
    metadata: Metadata
    content: str
