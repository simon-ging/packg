from pprint import pprint

import pytest

from packg.iotools.yamlext import dump_yaml, dumps_yaml, load_yaml, loads_yaml

_python_obj = {
    "model": {
        "model_factory": "open_clip",
        "model_ident": "hf-hub:laion/CLIP-ViT-L-14-DataComp.XL-s13B-b90K",
        "vis_preproc": {
            "preproc_factory": "open_clip",
            "preproc_ident": "hf-hub:laion/CLIP-ViT-L-14-DataComp.XL-s13B-b90K",
            "aug_cfg": None,
            "clip_pp_cfg": {
                "size": (224, 224),
                "mode": "RGB",
                "mean": [0.48145466, 0.4578275, 0.40821073],
                "std": [0.26862954, 0.26130258, 0.27577711],
                "interpolation": "bicubic",
                "resize_mode": "shortest",
                "fill_color": 0,
                "antialias": True,
            },
        },
    }
}


def test_dumps_yaml_standard_format_false():
    s = dumps_yaml(_python_obj, standard_format=False)
    pprint(s)


def test_dumps_yaml_standard_format_true():
    s = dumps_yaml(_python_obj, standard_format=True)
    pprint(s)
