import sys

from src.module_loader import ModuleLoader

from src.error_handler import ErrorHandler
from src.waifu_interpreter import WaifuInterpreter


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: waifu [path]")
        sys.exit(-1)
    path = sys.argv[1]

    try:
        error_handler = ErrorHandler()
        loader = ModuleLoader(error_handler)
        source = loader.read_source(path)
        waifu = WaifuInterpreter(loader, error_handler)
        waifu.run(source)

    except OSError:
        print(f"Could not load file at {path}.")
