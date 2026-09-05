# -*- coding: utf-8 -*-
"""电智学伴 Phase 2 - bge-small-zh 本地 embedding（chromadb EmbeddingFunction）"""
from functools import lru_cache

from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

import kb.config as cfg


@lru_cache(maxsize=1)
def _get_model():
    """全局单例：sentence-transformers 加载 bge-small-zh（CPU）。"""
    _configure_hf_offline_if_cached()
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(cfg.EMBED_MODEL, device=cfg.EMBED_DEVICE)
    return model


def _configure_hf_offline_if_cached() -> None:
    """模型已在本机缓存时自动转离线，避免联网超时重试拖慢首次查询。

    - 已缓存：HF_HUB_OFFLINE=1（直接读本地快照，不访问网络）
    - 未缓存：允许在线下载；国内默认走 hf-mirror 镜像（用户可自行覆盖 HF_ENDPOINT）
    """
    import glob
    import os

    if os.environ.get("HF_HUB_OFFLINE") == "1":
        return  # 用户已显式指定，尊重之
    try:
        cache_root = os.environ.get(
            "HF_HOME",
            os.path.join(os.path.expanduser("~"), ".cache", "huggingface"),
        )
        # 快照目录内存在 model.safetensors / pytorch_model.bin 即视为已缓存
        pattern = os.path.join(
            cache_root, "hub", "models--" + cfg.EMBED_MODEL.replace("/", "--"),
            "snapshots", "*", "model*.safetensors",
        )
        if glob.glob(pattern):
            os.environ["HF_HUB_OFFLINE"] = "1"
            return
    except Exception:
        pass
    os.environ.setdefault("HF_ENDPOINT", "https://hf-mirror.com")


class BGEEmbeddingFunction(EmbeddingFunction[Documents]):
    """chromadb 用：文档侧编码（不加指令前缀）。"""

    def __init__(self) -> None:
        super().__init__()

    def __call__(self, input: Documents) -> Embeddings:
        texts = [t if isinstance(t, str) else "" for t in input]
        if not texts:
            return []
        emb = _get_model().encode(texts, normalize_embeddings=True, batch_size=32)
        return emb.tolist()


def encode_query(query: str):
    """查询侧编码：bge 规范要求加指令前缀，检索相关性更准。"""
    emb = _get_model().encode(
        [cfg.QUERY_INSTRUCTION + query], normalize_embeddings=True
    )
    return emb.tolist()
