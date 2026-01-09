import json

from .path_manager import PathManager


def create_config(path_manager: PathManager, target_language: str = "English"):
    config = {
        "root_folder": path_manager.project_root,
        "pptx_folder": path_manager.file_folder,
        "pptx_name": path_manager.input_file,
        "working_dir": path_manager.working_dir,
        "extract_folder": path_manager.extracted_dir,
        "output_folder": path_manager.output_dir,
        "output_pptx": path_manager.output_pptx,
        "target_language": target_language,
    }

    # In frozen app, we cannot write to the config path (sys._MEIPASS)
    # We now pass config in-memory to pipelines.
    # with open(path_manager.get_config_path(), "w") as f:
    #     json.dump(config, f)

    return config
