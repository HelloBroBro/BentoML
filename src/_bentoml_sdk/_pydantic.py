from __future__ import annotations

import typing as t

from pydantic import GenerateSchema
from pydantic._internal import _known_annotated_metadata

from .typing_utils import get_args
from .typing_utils import get_origin
from .validators import ContentType
from .validators import DataframeSchema
from .validators import DType
from .validators import FileSchema
from .validators import PILImageEncoder
from .validators import Shape
from .validators import TensorSchema

if t.TYPE_CHECKING:
    from pydantic import ConfigDict

    Preparer: t.TypeAlias = t.Callable[
        [t.Any, t.Iterable[t.Any], ConfigDict], tuple[t.Any, list[t.Any]] | None
    ]
    import numpy as np
    import pandas as pd
    import tensorflow as tf
    import torch
    from PIL import Image
else:
    from bentoml._internal.utils.lazy_loader import LazyLoader

    np = LazyLoader("np", globals(), "numpy")
    tf = LazyLoader("tf", globals(), "tensorflow")
    torch = LazyLoader("torch", globals(), "torch")
    pd = LazyLoader("pd", globals(), "pandas")
    Image = LazyLoader("Image", globals(), "PIL.Image")


def numpy_prepare_pydantic_annotations(
    source: t.Any, annotations: t.Iterable[t.Any], config: ConfigDict
) -> tuple[t.Any, list[t.Any]] | None:
    if not getattr(source, "__module__", "").startswith("numpy"):
        return None

    origin = get_origin(source)

    if origin is not np.ndarray:
        return None

    args = get_args(source)
    try:
        dtype = np.dtype(get_args(args[1])[0]).name if args else None
    except TypeError:
        return None
    shape: tuple[int, ...] | None = None

    _, other_annotations = _known_annotated_metadata.collect_known_metadata(annotations)
    remaining_annotations = []
    for annotation in other_annotations:
        if isinstance(annotation, Shape):
            shape = annotation.dimensions
        elif isinstance(annotation, DType):
            if dtype is not None and dtype != annotation.dtype:
                raise ValueError(
                    f"Conflicting dtype annotations: {dtype} and {annotation.dtype}"
                )
            dtype = annotation.dtype
        else:
            remaining_annotations.append(annotation)
    return source, [TensorSchema("numpy-array", dtype, shape), *remaining_annotations]


def torch_prepare_pydantic_annotations(
    source: t.Any, annotations: t.Iterable[t.Any], config: ConfigDict
) -> tuple[t.Any, list[t.Any]] | None:
    if not getattr(source, "__module__", "").startswith("torch"):
        return None

    origin = get_origin(source)

    if not issubclass(origin, torch.Tensor):
        return None

    dtype: str | None = None
    shape: tuple[int, ...] | None = None

    _, remaining_annotations = _known_annotated_metadata.collect_known_metadata(
        annotations
    )
    for i, annotation in reversed(list(enumerate(remaining_annotations))):
        if isinstance(annotation, Shape):
            shape = annotation.dimensions
            del remaining_annotations[i]
        elif isinstance(annotation, DType):
            dtype = annotation.dtype
            del remaining_annotations[i]
    return source, [TensorSchema("torch-tensor", dtype, shape), *remaining_annotations]


def tf_prepare_pydantic_annotations(
    source: t.Any, annotations: t.Iterable[t.Any], config: ConfigDict
) -> tuple[t.Any, list[t.Any]] | None:
    if not getattr(source, "__module__", "").startswith("tensorflow"):
        return None

    origin = get_origin(source)
    if not issubclass(origin, tf.Tensor):
        return None

    dtype: str | None = None
    shape: tuple[int, ...] | None = None

    _, remaining_annotations = _known_annotated_metadata.collect_known_metadata(
        annotations
    )
    for i, annotation in reversed(list(enumerate(remaining_annotations))):
        if isinstance(annotation, Shape):
            shape = annotation.dimensions
            del remaining_annotations[i]
        elif isinstance(annotation, DType):
            dtype = annotation.dtype
            del remaining_annotations[i]
    return source, [TensorSchema("tf-tensor", dtype, shape), *remaining_annotations]


def pandas_prepare_pydantic_annotations(
    source: t.Any, annotations: t.Iterable[t.Any], config: ConfigDict
) -> tuple[t.Any, list[t.Any]] | None:
    if not getattr(source, "__module__", "").startswith("pandas"):
        return None

    origin = get_origin(source)
    if not issubclass(origin, pd.DataFrame):
        return None

    _, remaining_annotations = _known_annotated_metadata.collect_known_metadata(
        annotations
    )
    if not any(isinstance(a, DataframeSchema) for a in remaining_annotations):
        remaining_annotations.insert(0, DataframeSchema())
    return origin, remaining_annotations


def pil_prepare_pydantic_annotations(
    source: t.Any, annotations: t.Iterable[t.Any], _config: ConfigDict
) -> tuple[t.Any, list[t.Any]] | None:
    if not getattr(source, "__module__", "").startswith("PIL."):
        return None

    origin = get_origin(source) or source
    if not issubclass(origin, Image.Image):
        return None

    _, remaining_annotations = _known_annotated_metadata.collect_known_metadata(
        annotations
    )
    return origin, [PILImageEncoder(), *remaining_annotations]


def pathlib_prepare_pydantic_annotations(
    source: t.Any, annotations: t.Iterable[t.Any], _config: ConfigDict
) -> tuple[t.Any, list[t.Any]] | None:
    import pathlib

    if source not in {
        pathlib.PurePath,
        pathlib.PurePosixPath,
        pathlib.PureWindowsPath,
        pathlib.Path,
        pathlib.PosixPath,
        pathlib.WindowsPath,
    }:
        return None

    _, remaining_annotations = _known_annotated_metadata.collect_known_metadata(
        annotations
    )
    content_type: str | None = None
    for i, annotation in reversed(list(enumerate(remaining_annotations))):
        if isinstance(annotation, ContentType):
            content_type = annotation.content_type
            del remaining_annotations[i]
    return source, [FileSchema(content_type=content_type), *remaining_annotations]


CUSTOM_PREPARE_METHODS = [
    # tensors
    numpy_prepare_pydantic_annotations,
    torch_prepare_pydantic_annotations,
    tf_prepare_pydantic_annotations,
    # dataframe
    pandas_prepare_pydantic_annotations,
    # PIL image
    pil_prepare_pydantic_annotations,
]


class BentoMLPydanticGenerateSchema(GenerateSchema):
    def _get_prepare_pydantic_annotations_for_known_type(
        self, obj: t.Any, annotations: t.Iterable[t.Any]
    ) -> tuple[t.Any, list[t.Any]] | None:
        # Check for hashability
        try:
            hash(obj)
        except TypeError:
            # obj is definitely not a known type if this fails
            return None
        # try path preparer first to override the default one
        res = pathlib_prepare_pydantic_annotations(
            obj, annotations, self._config_wrapper.config_dict
        )
        if res is not None:
            return res

        res = super()._get_prepare_pydantic_annotations_for_known_type(obj, annotations)
        if res is not None:
            return res

        for preparer in CUSTOM_PREPARE_METHODS:
            res = preparer(obj, annotations, self._config_wrapper.config_dict)
            if res is not None:
                return res
        return None
